# from flask import Flask, render_template, Response
# from flask_socketio import SocketIO, emit
# import face_recognition
# import cv2
# import pandas as pd
# import numpy as np
# import os
# import datetime
#
# app = Flask(__name__)
# socketio = SocketIO(app)
#
# video = cv2.VideoCapture(0)  # Initialize your video capture device
#
# csv_file = 'known_faces.csv'
# df = pd.read_csv(csv_file) if os.path.exists(csv_file) else pd.DataFrame(
#     columns=['username', 'face_encoding', 'last_seen'])
#
#
# def save_known_faces():
#     df.to_csv(csv_file, index=False)
#
#
# def gen_frame():
#     global df
#     visible_faces = set()
#
#     while True:
#         _, frame = video.read()
#         face_locations = face_recognition.face_locations(frame)
#         face_encodings = face_recognition.face_encodings(frame, face_locations)
#         current_visible_faces = set()
#
#         for face_encoding, face_location in zip(face_encodings, face_locations):
#             if not df.empty:
#                 face_encodings_as_arrays = [np.array(eval(encoding)) for encoding in df['face_encoding'].tolist()]
#                 distances = face_recognition.face_distance(face_encodings_as_arrays, face_encoding)
#                 best_match_index = np.argmin(distances) if len(distances) > 0 else None
#
#                 if best_match_index is not None and distances[best_match_index] <= 0.6:
#                     username = df.at[best_match_index, 'username']
#                     last_seen_time = df.at[best_match_index, 'last_seen']
#                     current_visible_faces.add(username)
#
#                     top, right, bottom, left = face_location
#                     cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
#                     font = cv2.FONT_HERSHEY_DUPLEX
#                     # cv2.putText(frame, f'username: {username}', (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)
#                     cv2.putText(frame, f'last seen: {last_seen_time}', (left + 6, bottom + 15), font, 0.5,
#                                 (255, 255, 255), 1)
#                 else:
#                     new_face_id = f"face_{len(df) + 1}"
#                     current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                     new_row = pd.DataFrame({'username': [new_face_id], 'face_encoding': [str(face_encoding.tolist())],
#                                             'last_seen': [current_time_str]})
#                     df = pd.concat([df, new_row], ignore_index=True)
#                     save_known_faces()
#                     socketio.emit('last_seen_update', {
#                         'username': new_face_id,
#                         'last_seen': current_time_str
#                     })
#             else:
#                 new_face_id = f"face_1"
#                 current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                 df = pd.DataFrame({'username': [new_face_id], 'face_encoding': [str(face_encoding.tolist())],
#                                    'last_seen': [current_time_str]})
#                 save_known_faces()
#                 socketio.emit('last_seen_update', {
#                     'username': new_face_id,
#                     'last_seen': current_time_str
#                 })
#
#         faces_no_longer_visible = visible_faces - current_visible_faces
#         if faces_no_longer_visible:
#             for username in faces_no_longer_visible:
#                 best_match_index = df[df['username'] == username].index[0]
#                 current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                 df.at[best_match_index, 'last_seen'] = current_time_str
#                 socketio.emit('last_seen_update', {
#                     'username': username,
#                     'last_seen': current_time_str
#                 })
#             save_known_faces()
#
#         visible_faces = current_visible_faces
#
#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#
#
# @app.route('/video_feed')
# def video_feed():
#     return Response(gen_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')
#
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
#
# if __name__ == '__main__':
#     # port = int(os.environ.get("PORT", 33507))
#     # app.run(port=port)
#     port = int(os.environ.get("PORT", 5000))
#     socketio.run(app, host='0.0.0.0', port=port)


#
# from flask import Flask, render_template, Response
# from flask_socketio import SocketIO, emit
# import face_recognition
# import cv2
# import pandas as pd
# import numpy as np
# import os
# import datetime
# import time
#
# app = Flask(__name__)
# socketio = SocketIO(app)
#
# # video = cv2.VideoCapture(0)  # Initialize your video capture device
# video_index = cv2.CAP_ANY  # Use any available camera
# video = cv2.VideoCapture(video_index)
#
# csv_file = 'known_faces.csv'
# df = pd.read_csv(csv_file) if os.path.exists(csv_file) else pd.DataFrame(
#     columns=['username', 'face_encoding', 'last_seen'])
#
# # Constants
# MATCH_THRESHOLD = 0.5  # Adjust this value based on your testing, lower means more strict
# NEW_FACE_COOLDOWN = 5  # Time in seconds before a new face can be added again
#
# last_new_face_time = None  # Keep track of the last time a new face was added
#
#
# def save_known_faces():
#     df.to_csv(csv_file, index=False)
#
#
# def gen_frame():
#     global df, last_new_face_time
#     visible_faces = set()
#
#     while True:
#         _, frame = video.read()
#         face_locations = face_recognition.face_locations(frame)
#         face_encodings = face_recognition.face_encodings(frame, face_locations)
#         current_visible_faces = set()
#
#         for face_encoding, face_location in zip(face_encodings, face_locations):
#             if not df.empty:
#                 face_encodings_as_arrays = [np.array(eval(encoding)) for encoding in df['face_encoding'].tolist()]
#                 distances = face_recognition.face_distance(face_encodings_as_arrays, face_encoding)
#                 best_match_index = np.argmin(distances) if len(distances) > 0 else None
#
#                 if best_match_index is not None and distances[best_match_index] <= MATCH_THRESHOLD:
#                     username = df.at[best_match_index, 'username']
#                     last_seen_time = df.at[best_match_index, 'last_seen']
#                     current_visible_faces.add(username)
#
#                     top, right, bottom, left = face_location
#                     cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
#                     font = cv2.FONT_HERSHEY_DUPLEX
#                     cv2.putText(frame, f'last seen: {last_seen_time}', (left + 6, bottom + 15), font, 0.5,
#                                 (255, 255, 255), 1)
#                 else:
#                     current_time = datetime.datetime.now()
#                     if last_new_face_time is None or (
#                             current_time - last_new_face_time).total_seconds() > NEW_FACE_COOLDOWN:
#                         new_face_id = f"face_{len(df) + 1}"
#                         current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
#                         new_row = pd.DataFrame(
#                             {'username': [new_face_id], 'face_encoding': [str(face_encoding.tolist())],
#                              'last_seen': [current_time_str]})
#                         df = pd.concat([df, new_row], ignore_index=True)
#                         save_known_faces()
#                         socketio.emit('last_seen_update', {
#                             'username': new_face_id,
#                             'last_seen': current_time_str
#                         })
#                         last_new_face_time = current_time  # Update the last new face time
#                     else:
#                         print("A face was detected, but it's within the cooldown period.")
#             else:
#                 new_face_id = f"face_1"
#                 current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                 df = pd.DataFrame({'username': [new_face_id], 'face_encoding': [str(face_encoding.tolist())],
#                                    'last_seen': [current_time_str]})
#                 save_known_faces()
#                 socketio.emit('last_seen_update', {
#                     'username': new_face_id,
#                     'last_seen': current_time_str
#                 })
#
#         faces_no_longer_visible = visible_faces - current_visible_faces
#         if faces_no_longer_visible:
#             for username in faces_no_longer_visible:
#                 best_match_index = df[df['username'] == username].index[0]
#                 current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                 df.at[best_match_index, 'last_seen'] = current_time_str
#                 socketio.emit('last_seen_update', {
#                     'username': username,
#                     'last_seen': current_time_str
#                 })
#             save_known_faces()
#
#         visible_faces = current_visible_faces
#
#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#
#
# @app.route('/video_feed')
# def video_feed():
#     return Response(gen_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')
#
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
#
# if __name__ == '__main__':
#     # port = int(os.environ.get("PORT", 33507))
#     # app.run(port=port)
#     port = int(os.environ.get("PORT", 5000))
#     socketio.run(app, host='0.0.0.0', port=port)


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

def save_known_faces():
    df.to_csv(csv_file, index=False)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    global df  # Refer to the global df variable
    data = request.json
    image_data = data['image']
    image_data = image_data.split(",")[1]
    image_bytes = io.BytesIO(base64.b64decode(image_data))
    image = cv2.imdecode(np.frombuffer(image_bytes.read(), np.uint8), cv2.IMREAD_COLOR)

    # Process the frame for face recognition
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    for face_encoding in face_encodings:
        if not df.empty:
            # Compare the face encoding with known faces
            face_encodings_as_arrays = [np.array(eval(encoding)) for encoding in df['face_encoding'].tolist()]
            distances = face_recognition.face_distance(face_encodings_as_arrays, face_encoding)
            best_match_index = np.argmin(distances) if len(distances) > 0 else None

            if best_match_index is not None and distances[best_match_index] < 0.6:
                # Face recognized, update last seen time
                username = df.at[best_match_index, 'username']
                current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                df.at[best_match_index, 'last_seen'] = current_time_str
                save_known_faces()
                response = {'status': 'success', 'username': username, 'last_seen': current_time_str}
                return jsonify(response)
            else:
                # New face, add it to the known faces
                new_face_id = f"face_{len(df) + 1}"
                current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                new_row = pd.DataFrame(
                    {'username': [new_face_id], 'face_encoding': [str(face_encoding.tolist())],
                     'last_seen': [current_time_str]})
                df = pd.concat([df, new_row], ignore_index=True)
                save_known_faces()
                response = {'status': 'success', 'username': new_face_id, 'last_seen': current_time_str}
                return jsonify(response)
        else:
            # No known faces, add the new face
            new_face_id = f"face_1"
            current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df = pd.DataFrame({'username': [new_face_id], 'face_encoding': [str(face_encoding.tolist())],
                               'last_seen': [current_time_str]})
            save_known_faces()
            response = {'status': 'success', 'username': new_face_id, 'last_seen': current_time_str}
            return jsonify(response)

    # If no faces were recognized or added
    return jsonify({'status': 'no_faces'})

@app.route('/')
def index():
    return render_template('index.html')  # Assuming you have an index.html template

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
