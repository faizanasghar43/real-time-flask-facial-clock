import os
import io
import base64
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_assets import Environment, Bundle
from PIL import Image
import boto3
from botocore.exceptions import ClientError


# --- Config ---
REKOGNITION_COLLECTION = 'my-face-collection'

# Initialize Rekognition client using explicit credentials
rekognition = boto3.client(
    'rekognition',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
)

def ensure_collection_exists():
    try:
        response = rekognition.describe_collection(CollectionId=REKOGNITION_COLLECTION)
        print(f"✅ Rekognition collection '{REKOGNITION_COLLECTION}' already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"🚀 Creating Rekognition collection '{REKOGNITION_COLLECTION}'...")
            rekognition.create_collection(CollectionId=REKOGNITION_COLLECTION)
            print("✅ Collection created.")
        else:
            raise e

# --- Flask Setup ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
assets = Environment(app)

opacity_flag = False

# --- AWS Rekognition Client ---
# rekognition = boto3.client('rekognition', region_name='us-east-1')

# --- Flask-Assets for SCSS ---
scss_bundle = Bundle('main.scss', filters='libsass', output='styles.css', depends='*.scss')
assets.register('scss_all', scss_bundle)
scss_bundle.build()

# --- DB Model ---
class KnownFace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    last_seen = db.Column(db.DateTime, nullable=False)

# --- Helper: Index Face ---
def index_face(username, image_bytes):
    rekognition.index_faces(
        CollectionId=REKOGNITION_COLLECTION,
        Image={'Bytes': image_bytes},
        ExternalImageId=username,
        DetectionAttributes=['DEFAULT']
    )

    now_minus_4_hours = datetime.now() - timedelta(hours=4)
    known_face = KnownFace.query.filter_by(username=username).first()
    if known_face:
        known_face.last_seen = now_minus_4_hours
    else:
        known_face = KnownFace(username=username, last_seen=now_minus_4_hours)
        db.session.add(known_face)

    db.session.commit()
    return "Face indexed and stored."

# --- Helper: Search Face ---
def search_face(image_bytes):
    try:
        response = rekognition.search_faces_by_image(
            CollectionId=REKOGNITION_COLLECTION,
            Image={'Bytes': image_bytes},
            MaxFaces=1,
            FaceMatchThreshold=95
        )
        if response['FaceMatches']:
            match = response['FaceMatches'][0]
            username = match['Face']['ExternalImageId']
            known_face = KnownFace.query.filter_by(username=username).first()
            last_seen = known_face.last_seen if known_face else None
            if known_face:
                known_face.last_seen = datetime.now() - timedelta(hours=4)
                db.session.commit()
            return {'match': True, 'username': username, 'last_seen': last_seen}
        return {'match': False}
    except Exception as e:
        return {'error': str(e)}

# --- Routes ---
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
        image_file = request.files['image_file']
        image_bytes = image_file.read()
        message = index_face(username, image_bytes)
        return jsonify({'status': 'success', 'message': message})
    return render_template('add_face.html')

@app.route('/compare_face', methods=['POST'])
def compare_face():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({'status': 'error', 'message': 'Image data missing'}), 400

    try:
        image_data = data['image'].split(",")[1]
        image_bytes = base64.b64decode(image_data)
        result = search_face(image_bytes)

        if result.get('error'):
            return jsonify({'status': 'error', 'message': result['error']})
        if result['match']:
            return jsonify({'status': 'success', 'match': True, 'username': result['username'],
                            'last_seen': result['last_seen'].isoformat() if result['last_seen'] else None})
        else:
            return jsonify({'status': 'success', 'match': False, 'message': 'Face not recognized.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/add_info', methods=['GET', 'POST'])
def add_info():
    if request.method == 'POST':
        username = request.form['username']
        image_data = request.form.get('image')
        if image_data:
            image_bytes = base64.b64decode(image_data.split(",")[1])
            message = index_face(username, image_bytes)
            return render_template('ThanksPage.html', message=message, status='success')
        else:
            return render_template('ThanksPage.html', message='No image data provided.', status='error')
    return render_template('add_face.html')

@app.route('/about')
def about():
    return render_template('about.html')

# --- Run Server ---
if __name__ == '__main__':
    from sys import argv

    if 'db_init' in argv:
        with app.app_context():  # ✅ Fix: wrap in context
            db.create_all()
            print("✅ Tables created.")
    else:
        ensure_collection_exists()
        app.run(debug=True)
