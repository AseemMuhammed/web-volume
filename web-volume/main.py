from flask import Flask, render_template, Response

from multiprocessing import Process, Queue
import cv2
import mediapipe as mp
import math
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

app = Flask(__name__)

# Global variables for volume control process
volume_control_process = None
volume_control_queue = None

def volume_control(queue):
    # Volume Control Logic
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_hands = mp.solutions.hands

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volRange = volume.GetVolumeRange()
    minVol, maxVol, volBar, volPer = volRange[0], volRange[1], 400, 0

    wCam, hCam = 640, 480
    cam = cv2.VideoCapture(0)
    cam.set(3, wCam)
    cam.set(4, hCam)

    with mp_hands.Hands(
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5) as hands:

        while True:
            success, image = cam.read()

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        mp_drawing_styles.get_default_hand_landmarks_style(),
                        mp_drawing_styles.get_default_hand_connections_style()
                    )

            lmList = []
            if results.multi_hand_landmarks:
                myHand = results.multi_hand_landmarks[0]
                for id, lm in enumerate(myHand.landmark):
                    h, w, c = image.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lmList.append([id, cx, cy])

            if len(lmList) != 0:
                x1, y1 = lmList[4][1], lmList[4][2]
                x2, y2 = lmList[8][1], lmList[8][2]

                cv2.circle(image, (x1, y1), 15, (255, 255, 255))
                cv2.circle(image, (x2, y2), 15, (255, 255, 255))
                cv2.line(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                length = math.hypot(x2 - x1, y2 - y1)
                if length < 50:
                    cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 3)

                vol = np.interp(length, [50, 220], [minVol, maxVol])
                volume.SetMasterVolumeLevel(vol, None)
                volBar = np.interp(length, [50, 220], [400, 150])
                volPer = np.interp(length, [50, 220], [0, 100])

                cv2.rectangle(image, (50, 150), (85, 400), (0, 0, 0), 3)
                cv2.rectangle(image, (50, int(volBar)), (85, 400), (0, 0, 0), cv2.FILLED)
                cv2.putText(image, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                            1, (0, 0, 0), 3)

            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()
            queue.put(frame)

    cam.release()

@app.route('/')
def index():
    return render_template('index.html')  # Assuming you have an index.html file in your templates directory

@app.route('/video_feed')
def video_feed():
    global volume_control_process, volume_control_queue

    if volume_control_process is None or not volume_control_process.is_alive():
        volume_control_queue = Queue()
        volume_control_process = Process(target=volume_control, args=(volume_control_queue,))
        volume_control_process.start()

    def generate():
        while volume_control_process.is_alive():
            frame = volume_control_queue.get()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
