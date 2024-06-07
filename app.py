from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import numpy as np
import face_recognition
import cv2
import base64
import io
from PIL import Image
from flask_assets import Environment, Bundle
import pytz
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("://", "ql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
assets = Environment(app)
opacity_flag = False  # By default, do not alter the opacity

# create bundle for Flask-Assets to compile and prefix scss to css
scss_bundle = Bundle(
    'main.scss',  # Path to your main SCSS file
    filters='libsass',  # Use libsass to compile SCSS to CSS
    output='styles.css',  # Output path for the compiled CSS
    depends='*.scss'  # Ensure changes in any SCSS files trigger a recompile
)

# Register and build the bundle
assets.register('scss_all', scss_bundle)
scss_bundle.build()


# Model for storing known faces
class KnownFace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    face_encoding = db.Column(db.PickleType, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<KnownFace {self.username}>'


#
#
# @app.before_request
# def create_tables():
#     db.create_all()


# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/')
def index():
    return render_template('index.html', opacity_flag=opacity_flag)

@app.route('/set-opacity-zero', methods=['POST'])
def set_opacity_zero():
    global opacity_flag
    opacity_flag = True  # Set the flag to indicate opacity should be zero
    return jsonify({'status': 'success', 'message': 'Homepage opacity will be set to zero.'})


@app.route('/face', methods=['GET', 'POST'])
def add_face():
    if request.method == 'POST':
        username = request.form['username']
        image_file = request.files['image_file']
        image = face_recognition.load_image_file(image_file)
        face_encodings = face_recognition.face_encodings(image)

        if face_encodings:
            message = add_or_update_face(username, face_encodings[0])
            return jsonify({'status': 'success', 'message': message})
            # return render_template('ThanksPage.html', message=message)
        else:
            return jsonify({'status': 'error', 'message': 'No faces found in the image.'})
    return render_template('add_face.html')


@app.route('/compare_face', methods=['POST'])
def compare_face():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({'status': 'error', 'message': 'Image data missing.'}), 400

    image_data = data['image'].split(",")[1]
    image_bytes = io.BytesIO(base64.b64decode(image_data))
    image = Image.open(image_bytes)
    image_array = np.array(image.convert('RGB'))

    # Attempt to find faces in the image
    face_locations = face_recognition.face_locations(image_array)
    face_encodings = face_recognition.face_encodings(image_array, face_locations)

    if face_encodings:
        # Iterate over each face found in the image
        for face_encoding in face_encodings:
            # Attempt to match each face encoding to known faces
            matches = face_recognition.compare_faces([face.face_encoding for face in KnownFace.query.all()],
                                                     face_encoding)
            face_distances = face_recognition.face_distance([face.face_encoding for face in KnownFace.query.all()],
                                                            face_encoding)
            best_match_index = np.argmin(face_distances) if len(face_distances) > 0 else None

            if best_match_index is not None and matches[best_match_index]:
                # A match was found, update last_seen
                known_face = KnownFace.query.all()[best_match_index]
                last_seen=known_face.last_seen
                eastern = pytz.timezone('US/Eastern')
                known_face.last_seen = datetime.now(tz=eastern)
                db.session.commit()
                print({'status': 'success', 'match': True, 'username': known_face.username,
                       'last_seen': last_seen.isoformat()})
                return jsonify({'status': 'success', 'match': True, 'username': known_face.username,
                                'last_seen': last_seen.isoformat()})

            else:
                # No match found
                print({'status': 'success', 'match': False,
                       'message': 'Your face is not recognized. Please add your face.'})
                return jsonify({'status': 'success', 'match': False,
                                'message': 'Your face is not recognized. Please add your face.'})
    else:
        print({'status': 'error', 'message': 'No faces found in the submitted image.'})
        # No faces found in the image
        return jsonify({'status': 'error', 'message': 'No faces found in the submitted image.'})


def add_or_update_face(username, face_encoding):
    eastern = pytz.timezone('US/Eastern')
    now_in_eastern = datetime.now(tz=eastern)

    known_face = KnownFace.query.filter_by(username=username).first()
    if known_face:
        # If the face is already in the database, update the last seen and face encoding
        known_face.face_encoding = face_encoding
        known_face.last_seen = now_in_eastern
        message = "Your face is already there. Information updated."
    else:
        # If the face is not in the database, add it
        known_face = KnownFace(username=username, face_encoding=face_encoding, last_seen=now_in_eastern)
        db.session.add(known_face)
        message = "New face added successfully."

    db.session.commit()
    return message

@app.route('/about')
def about():
    return render_template('about.html')


# @app.route('/thank_you')
# def thank_you(msg):
#
#     return render_template('ThanksPage.html', message=msg)




@app.route('/add_info', methods=['GET', 'POST'])
def add_info():
    if request.method == 'POST':
        username = request.form['username']
        image_data = request.form.get('image')

        # Decode the Base64 image
        if image_data:
            image_data = image_data.split(",")[1]  # Remove the Base64 header if present
            image_bytes = base64.b64decode(image_data)
            image = face_recognition.load_image_file(io.BytesIO(image_bytes))
            face_encodings = face_recognition.face_encodings(image)

            if face_encodings:
                # Only consider the first face found in the image for this example
                face_encoding = face_encodings[0]
                add_or_update_face(username, face_encoding)
                # return jsonify({'status': 'success', 'message': 'Face added/updated successfully.'})
                return render_template('ThanksPage.html', message="Face added/updated successfully.", status='success')
            else:
                # return jsonify({'status': 'error', 'message': })
                return render_template('ThanksPage.html', message='No faces found in the submitted image.', status='error')

        else:
            # return jsonify({'status': 'error', 'message': })
            return render_template('ThanksPage.html', message='No image data provided.', status='error')

    # Render a form for GET request
    return render_template('add_face.html')

@app.route('/reset-opacity', methods=['POST'])
def reset_opacity():
    global opacity_flag
    opacity_flag = False  # Reset the flag
    return jsonify({'status': 'success', 'message': 'Homepage opacity reset to default.'})

if __name__ == '__main__':
    app.run(debug=True)
