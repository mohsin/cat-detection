import io
import os
import cv2
import subprocess
import time
import boto3
import datetime
import picamera
import picamera.array
import numpy as np
from PIL import Image

class CaptureHandler:
    def __init__(self, camera, stream):
        self.camera = camera
        self.stream = stream
        self.motion_count = 0
        self.motion_last_detected = time.time()
        self.motion_detected = False
        self.previous_frame = None
        self.current_frame = None
        self.recording = False

    def tick(self):
        stream = io.BytesIO()
        self.camera.capture(stream, format='jpeg', use_video_port=True)
        stream.seek(0)
        self.current_frame = stream
        self.detect_motion()

        if not self.recording:
            if self.motion_detected:
                count = 0
                self.recording = True

                # Ensure folder to save captures exists
                path = '/home/mohsin/cat-detector/captures/%s/' % datetime.datetime.now().date()
                os.makedirs(path, exist_ok = True)

                # Split the recording to store into file instead.
                self.camera.split_recording(path + datetime.datetime.now().strftime('%H%M') + '-' + str(self.motion_count) + '-' + 'motion.h264')
                print('Recording started')

                # If motion is still there or has been in the past 5 seconds, continue recording.
                while time.time() - self.motion_last_detected < 5 or self.motion_detected:
                    if (count == 0 or count % 10 == 0):
                        self.play_sound_if_cat()
                    else:
                        self.tick()
                    count += 1
                    self.camera.wait_recording(1)

                # Split the recording back to the circular buffer.
                self.camera.split_recording(self.stream)
                print('Finished capturing motion #' + str(self.motion_count))

                self.motion_count += 1
                self.recording = False
                print('Recording complete')

    def detect_motion(self):
        # Initially, set the motion detected to false
        self.motion_detected = False

        # 1. Get the image of current frame as array
        image = Image.open(self.current_frame)
        image_data = np.asarray(image)

        # 2. Prepare image; grayscale and blur
        prepared_frame = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        prepared_frame = cv2.GaussianBlur(src=prepared_frame, ksize=(5, 5), sigmaX=0)

        # 3. If first frame, just return
        if (self.previous_frame is None):
            # First frame; there is no previous one yet
            self.previous_frame = prepared_frame
        else:
            # 4. Calculate difference and update previous frame
            diff_frame = cv2.absdiff(src1=self.previous_frame, src2=prepared_frame)
            self.previous_frame = prepared_frame

            # 5. Dilute the image a bit to make differences more seeable; more suitable for contour detection
            kernel = np.ones((5, 5))
            diff_frame = cv2.dilate(diff_frame, kernel, 1)

            # 6. Only take different areas that are different enough (>20 / 255)
            thresh_frame = cv2.threshold(src=diff_frame, thresh=20, maxval=255, type=cv2.THRESH_BINARY)[1]

            # 7. Find contours, count them and if they're above a threshold, motion exists.
            contours, _ = cv2.findContours(image=thresh_frame, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) > 4:
                self.motion_last_detected = time.time()
                self.motion_detected = True

    def play_sound_if_cat(self):
        with open ('/home/mohsin/cat-detector/apicount.txt', 'r') as f:
            current_count = int(f.read().strip())
            print('Current API count: ' + str(current_count))

        client = boto3.client('rekognition')
        response = client.detect_labels(Image={'Bytes': self.current_frame.getvalue()})
        cat_label = [label for label in response['Labels'] if label.get('Name') == 'Cat'] 
        if (cat_label):
            if (cat_label[0]['Confidence']) > 75.0:
                proc = subprocess.Popen(['aplay', '-D', 'bluealsa', '/home/mohsin/cat-detector/dog.wav'])
                try:
                    outs, errs = proc.communicate(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate()

        # Raise the API call count
        current_count += 1
        with open('/home/mohsin/cat-detector/apicount.txt', 'w') as f:
            f.write(str(current_count) + "\n")

class CatDetector:
    def __init__(self):
        with picamera.PiCamera() as camera:
                camera.resolution = (1920, 1080)
                camera.framerate = 30
                stream = picamera.PiCameraCircularIO(camera, seconds=10)
                handler = CaptureHandler(camera, stream)
                camera.start_recording(stream, format='h264')
                time.sleep(2)
                try:
                    while True:
                        handler.tick()
                        time.sleep(1)
                except KeyboardInterrupt:
                    print('Used interruped. Exiting...')
                finally:
                    camera.stop_recording()
