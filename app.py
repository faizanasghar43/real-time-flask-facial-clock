from flask import Flask, request, jsonify, render_template
import face_recognition
import cv2
import pandas as pd
import numpy as np
import os
import datetime
import base64
import io

app = Flask(__name__)

csv_file = 'known_faces.csv'
df = pd.read_csv(csv_file) if os.path.exists(csv_file) else pd.DataFrame(
    columns=['username', 'face_encoding', 'last_seen'])

MATCH_THRESHOLD = 0.5
visible_faces = set()
last_new_face_time = None
NEW_FACE_COOLDOWN = 5


def save_known_faces(df):
    df.to_csv(csv_file, index=False)


@app.route('/process_frame', methods=['POST'])
def process_frame():
    global df, visible_faces, last_new_face_time

    data = request.json
    image_data = data['image']
    image_data = image_data.split(",")[1]
    image_bytes = io.BytesIO(base64.b64decode(image_data))
    image = cv2.imdecode(np.frombuffer(image_bytes.read(), np.uint8), cv2.IMREAD_COLOR)

    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)
    current_visible_faces = set()

    for face_encoding, face_location in zip(face_encodings, face_locations):
        if not df.empty:
            face_encodings_as_arrays = [np.array(eval(encoding)) for encoding in df['face_encoding'].tolist()]
            distances = face_recognition.face_distance(face_encodings_as_arrays, face_encoding)
            best_match_index = np.argmin(distances) if len(distances) > 0 else None

            if best_match_index is not None and distances[best_match_index] <= MATCH_THRESHOLD:
                username = df.at[best_match_index, 'username']
                current_visible_faces.add(username)

                if username not in visible_faces:
                    current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    df.at[best_match_index, 'last_seen'] = current_time_str
                    save_known_faces(df)

            else:
                current_time = datetime.datetime.now()
                if last_new_face_time is None or (
                        current_time - last_new_face_time).total_seconds() > NEW_FACE_COOLDOWN:
                    new_face_id = f"face_{len(df) + 1}"
                    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
                    new_row = pd.DataFrame(
                        {'username': [new_face_id], 'face_encoding': [str(face_encoding.tolist())],
                         'last_seen': [current_time_str]})
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_known_faces(df)
                    last_new_face_time = current_time
        else:
            new_face_id = f"face_1"
            current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df = pd.DataFrame({'username': [new_face_id], 'face_encoding': [str(face_encoding.tolist())],
                               'last_seen': [current_time_str]})
            save_known_faces(df)

    faces_no_longer_visible = visible_faces - current_visible_faces
    for username in faces_no_longer_visible:
        best_match_index = df[df['username'] == username].index[0]
        current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        df.at[best_match_index, 'last_seen'] = current_time_str
        save_known_faces(df)

    visible_faces = current_visible_faces

    return jsonify({'status': 'success',
                    'last_seen': last_new_face_time})


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
