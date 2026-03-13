import webbrowser
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from flask import Flask, render_template, Response
import cv2
from ultralytics import YOLO
import threading
import time

app = Flask(__name__)

model = YOLO("yolov8n")

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FPS, 20)
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

ignore_classes = ["person"]

frame = None
boxes = []
frame_id = 0


# ---------------- CAMERA THREAD ----------------
def camera_thread():
    global frame

    while True:
        ret, img = camera.read()
        if not ret:
            continue

        frame = cv2.resize(img, (640,480))


# ---------------- DETECTION THREAD ----------------
def detection_thread():
    global frame, boxes, frame_id

    while True:

        if frame is None:
            time.sleep(0.01)
            continue

        frame_id += 1

        # Run YOLO every 3 frames
        if frame_id % 3 != 0:
            time.sleep(0.01)
            continue

        results = model(frame, verbose=False)

        new_boxes = []

        for r in results:
            for box in r.boxes:

                cls = int(box.cls[0])
                label = model.names[cls]

                if label in ignore_classes:
                    continue

                x1,y1,x2,y2 = map(int,box.xyxy[0])
                new_boxes.append((x1,y1,x2,y2))

        boxes = new_boxes

        time.sleep(0.02)


# ---------------- VIDEO STREAM ----------------
def generate_frames():

    while True:

        if frame is None:
            continue

        display = frame.copy()
        count = 0

        for (x1,y1,x2,y2) in boxes:

            # Draw bounding box only
            cv2.rectangle(display,(x1,y1),(x2,y2),(0,255,0),2)

            count += 1

        # Show only object count
        cv2.putText(display,
            f"Objects: {count}",
            (20,60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0,0,255),
            3,
            cv2.LINE_AA)

        ret, buffer = cv2.imencode('.jpg', display)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


# ---------------- ROUTES ----------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# ---------------- MAIN ----------------
if __name__ == "__main__":

    threading.Thread(target=camera_thread, daemon=True).start()
    threading.Thread(target=detection_thread, daemon=True).start()

    url = "http://127.0.0.1:5000"

    print("\nOpen:", url)

    webbrowser.open(url)

    app.run(debug=False, threaded=True)









# <<.............................................this is a finger counting code..............................................>>






# from flask import Flask, render_template, Response
# import cv2
# import numpy as np
# import mediapipe as mp
# import time

# app = Flask(__name__)

# camera = cv2.VideoCapture(0)
# time.sleep(2)

# kernel = np.ones((3,3), np.uint8)

# # Mediapipe setup
# mp_hands = mp.solutions.hands
# hands = mp_hands.Hands(max_num_hands=1)
# mp_draw = mp.solutions.drawing_utils

# def count_fingers(hand_landmarks):

#     finger_tips = [4, 8, 12, 16, 20]
#     fingers = []

#     # Thumb
#     if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x:
#         fingers.append(1)
#     else:
#         fingers.append(0)

#     # Other fingers
#     for tip in [8,12,16,20]:
#         if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip-2].y:
#             fingers.append(1)
#         else:
#             fingers.append(0)

#     return sum(fingers)

# def generate_frames():

#     while True:

#         success, frame = camera.read()
#         if not success:
#             continue

#         frame = cv2.resize(frame,(640,480))
#         display = frame.copy()

#         # ---------- HAND DETECTION ----------
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = hands.process(rgb)

#         finger_count = 0
#         hand_present = False

#         if results.multi_hand_landmarks:

#             hand_present = True

#             for handLms in results.multi_hand_landmarks:
#                 mp_draw.draw_landmarks(display, handLms, mp_hands.HAND_CONNECTIONS)

#                 finger_count = count_fingers(handLms)

#         # ---------- OBJECT DETECTION ----------
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         blur = cv2.GaussianBlur(gray,(5,5),0)

#         thresh = cv2.adaptiveThreshold(
#             blur,
#             255,
#             cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#             cv2.THRESH_BINARY_INV,
#             11,
#             2
#         )

#         opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
#         closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=2)

#         contours,_ = cv2.findContours(
#             closing,
#             cv2.RETR_EXTERNAL,
#             cv2.CHAIN_APPROX_SIMPLE
#         )

#         object_count = 0

#         for cnt in contours:

#             area = cv2.contourArea(cnt)

#             if area > 2000:
#                 x,y,w,h = cv2.boundingRect(cnt)

#                 # Ignore hand area
#                 if not hand_present:
#                     object_count += 1
#                     cv2.rectangle(display,(x,y),(x+w,y+h),(0,255,0),2)

#         # ---------- TEXT DISPLAY ----------
#         cv2.putText(display,
#                     f"Objects: {object_count}",
#                     (20,40),
#                     cv2.FONT_HERSHEY_SIMPLEX,
#                     1,
#                     (0,0,255),
#                     2)

#         if hand_present:
#             cv2.putText(display,
#                         f"Fingers: {finger_count}",
#                         (20,80),
#                         cv2.FONT_HERSHEY_SIMPLEX,
#                         1,
#                         (255,0,0),
#                         2)

#         ret, buffer = cv2.imencode('.jpg', display)
#         frame = buffer.tobytes()

#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/video_feed')
# def video_feed():
#     return Response(generate_frames(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')

# if __name__ == "__main__":
#     app.run(debug=True, threaded=True)