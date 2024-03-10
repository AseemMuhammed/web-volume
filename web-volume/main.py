from flask import Flask, render_template, Response
import cv2
import mediapipe as mp
import math
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

import volume 

app = Flask(__name__)

# Flag to indicate whether to continue video feed
continue_video_feed = True

@app.route('/')
def index():
    return render_template('index.html')  # Assuming you have an index.html file in your templates directory
@app.route('/video_feed')
def video_feed():
    volume.main()  # Run the main function from volume.py
    return 'Volume control executed'  # Response indicating the task is completed

@app.route('/stop_video_feed')
def stop_video_feed():
    volume.stop()  # Call a function in volume.py to stop the execution
    return 'Volume control stopped'  #

if __name__ == '__main__':
    app.run(debug=True)
