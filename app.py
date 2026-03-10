from flask import Flask, render_template, Response
import cv2
import numpy as np
import time

app = Flask(__name__)

camera = cv2.VideoCapture(0)
time.sleep(2)

kernel = np.ones((5,5),np.uint8)

# Load face detector
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


def detect_shape(cnt):

    shape = "object"

    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

    vertices = len(approx)

    if vertices == 3:
        shape = "Triangle"

    elif vertices == 4:
        x,y,w,h = cv2.boundingRect(approx)
        aspectRatio = w / float(h)

        if 0.95 <= aspectRatio <= 1.05:
            shape = "Square"
        else:
            shape = "Rectangle"

    elif vertices > 6:
        shape = "Circle"

    return shape


def generate_frames():

    while True:

        success, frame = camera.read()
        if not success:
            continue

        frame = cv2.resize(frame,(640,480))
        display = frame.copy()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ---------- REMOVE FACE ----------
        faces = face_cascade.detectMultiScale(gray,1.3,5)

        for (x,y,w,h) in faces:
            cv2.rectangle(gray,(x,y),(x+w,y+h),(0,0,0),-1)
            cv2.rectangle(display,(x,y),(x+w,y+h),(0,0,0),-1)

        # ---------- OBJECT DETECTION ----------
        blur = cv2.GaussianBlur(gray,(5,5),0)

        edges = cv2.Canny(blur,50,150)

        edges = cv2.dilate(edges,kernel,iterations=2)
        edges = cv2.erode(edges,kernel,iterations=1)

        contours,_ = cv2.findContours(edges,
                                      cv2.RETR_EXTERNAL,
                                      cv2.CHAIN_APPROX_SIMPLE)

        count = 0

        for cnt in contours:

            area = cv2.contourArea(cnt)

            if area > 3000:

                x,y,w,h = cv2.boundingRect(cnt)

                # Ignore tall vertical shapes (like body/hand)
                if h/w < 2.5:

                    shape = detect_shape(cnt)

                    cv2.rectangle(display,(x,y),(x+w,y+h),(0,255,0),2)

                    cv2.putText(display,
                                shape,
                                (x,y-10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (255,0,0),
                                2)

                    count += 1

        cv2.putText(display,
                    f"Objects: {count}",
                    (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,0,255),
                    2)

        ret, buffer = cv2.imencode('.jpg', display)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    app.run(debug=True, threaded=True)




















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