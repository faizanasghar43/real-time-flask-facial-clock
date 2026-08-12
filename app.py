import os
import io
import base64
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_assets import Environment, Bundle
from PIL import Image
from insightface.app import FaceAnalysis

SIMILARITY_THRESHOLD = 0.4

face_app = FaceAnalysis(name='buffalo_sc', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(320, 320))

app = Flask(__name__)
db_url = os.environ.get('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
assets = Environment(app)
opacity_flag = False

scss_bundle = Bundle('main.scss', filters='libsass', output='styles.css', depends='*.scss')
assets.register('scss_all', scss_bundle)
scss_bundle.build()


class KnownFace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    face_encoding = db.Column(db.LargeBinary, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)


def _get_embedding(image_bytes):
    img = np.array(Image.open(io.BytesIO(image_bytes)).convert('RGB'))
    faces = face_app.get(img)
    return faces[0].normed_embedding if faces else None


def index_face(username, image_bytes):
    emb = _get_embedding(image_bytes)
    if emb is None:
        raise ValueError('No face detected in image')

    now_minus_4h = datetime.now() - timedelta(hours=4)
    known_face = KnownFace.query.filter_by(username=username).first()
    if known_face:
        known_face.face_encoding = emb.astype(np.float32).tobytes()
        known_face.last_seen = now_minus_4h
    else:
        known_face = KnownFace(
            username=username,
            face_encoding=emb.astype(np.float32).tobytes(),
            last_seen=now_minus_4h
        )
        db.session.add(known_face)
    db.session.commit()
    return 'Face indexed and stored.'


def search_face(image_bytes):
    emb = _get_embedding(image_bytes)
    if emb is None:
        return {'error': 'No face detected in image'}

    known_faces = KnownFace.query.all()
    if not known_faces:
        return {'match': False}

    best_score, best_face = -1, None
    for kf in known_faces:
        stored = np.frombuffer(kf.face_encoding, dtype=np.float32)
        score = float(np.dot(emb, stored))
        if score > best_score:
            best_score, best_face = score, kf

    if best_score >= SIMILARITY_THRESHOLD:
        last_seen = best_face.last_seen
        best_face.last_seen = datetime.now() - timedelta(hours=4)
        db.session.commit()
        return {'match': True, 'username': best_face.username, 'last_seen': last_seen}
    return {'match': False}


@app.route('/')
def index():
    return render_template('index.html', opacity_flag=opacity_flag)


@app.route('/set-opacity-zero', methods=['POST'])
def set_opacity_zero():
    global opacity_flag
    opacity_flag = True
    return jsonify({'status': 'success', 'message': 'Opacity set to zero'})


@app.route('/reset-opacity', methods=['POST'])
def reset_opacity():
    global opacity_flag
    opacity_flag = False
    return jsonify({'status': 'success', 'message': 'Opacity reset to default'})


@app.route('/face', methods=['GET', 'POST'])
def add_face():
    if request.method == 'POST':
        username = request.form['username']
        image_bytes = request.files['image_file'].read()
        try:
            message = index_face(username, image_bytes)
            return jsonify({'status': 'success', 'message': message})
        except ValueError as e:
            return jsonify({'status': 'error', 'message': str(e)})
    return render_template('add_face.html')


@app.route('/compare_face', methods=['POST'])
def compare_face():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({'status': 'error', 'message': 'Image data missing'}), 400
    try:
        image_bytes = base64.b64decode(data['image'].split(',')[1])
        result = search_face(image_bytes)
        if result.get('error'):
            return jsonify({'status': 'error', 'message': result['error']})
        if result['match']:
            return jsonify({'status': 'success', 'match': True,
                            'username': result['username'],
                            'last_seen': result['last_seen'].isoformat() if result['last_seen'] else None})
        return jsonify({'status': 'success', 'match': False, 'message': 'Face not recognized.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/add_info', methods=['GET', 'POST'])
def add_info():
    if request.method == 'POST':
        username = request.form['username']
        image_data = request.form.get('image')
        if image_data:
            image_bytes = base64.b64decode(image_data.split(',')[1])
            try:
                message = index_face(username, image_bytes)
                return render_template('ThanksPage.html', message=message, status='success')
            except ValueError as e:
                return render_template('ThanksPage.html', message=str(e), status='error')
        return render_template('ThanksPage.html', message='No image data provided.', status='error')
    return render_template('add_face.html')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    if 'db_init' in __import__('sys').argv:
        with app.app_context():
            db.create_all()
            print('Tables created.')
    else:
        app.run(debug=True)
