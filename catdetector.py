import io
import os
import signal
import subprocess
import time
import boto3
import datetime
import picamera
import picamera.array
import numpy as np
from PIL import Image

class CaptureHandler:
    def __init__(self, camera, stream, post_capture_callback=None):
        self.camera = camera
        self.stream = stream
        self.callback = post_capture_callback
        self.detected = False
        self.working = False
        self.i = 0

    def motion_detected(self):
        self.last_detected = time.time()
        if not self.working:
            self.detected = True

    def play_sound_if_cat(self):
        self.stream = io.BytesIO()
        with open ('apicount.txt', 'r') as f:
            current_count = int(f.read().strip())
            print("Current API count: " + str(current_count))
        self.camera.capture(self.stream, format='jpeg', use_video_port=True)
        self.stream.seek(0)
        possible_cat = Image.open(self.stream)

        client = boto3.client('rekognition')
        response = client.detect_labels(Image={'Bytes': self.stream.getvalue()})
        cat_label = [label for label in response['Labels'] if label.get('Name') == 'Cat'] 
        if (cat_label):
            if (cat_label[0]['Confidence']) > 75.0:
                proc = subprocess.Popen(['aplay', '-D', 'bluealsa', 'dog.wav'])
                try:
                    outs, errs = proc.communicate(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    outs, errs = proc.communicate()

        # Raise the API call count
        current_count += 1
        with open('apicount.txt', 'w') as f:
            f.write(str(current_count) + "\n")

    def tick(self):
        if self.detected:
            count = 0
            self.working = True
            self.detected = False
            print('Recording started')

            path = "captures/%s/" % datetime.datetime.now().date()

            os.makedirs(path, exist_ok = True)

            self.camera.split_recording(path + datetime.datetime.now().strftime("%H%M") + '-' + str(self.i) + '-' + 'motion.h264')
            while time.time() - self.last_detected < 5 or self.detected:
                if (count == 0 or count % 10 == 0):
                    self.play_sound_if_cat()
                count += 1
                self.camera.wait_recording(1)

            print('Recording complete')

            self.camera.split_recording(self.stream)
            print("Finished capturing motion #" + str(self.i))

            self.i += 1
            self.working = False

class MyMotionDetector(picamera.array.PiMotionAnalysis):
    def __init__(self, camera, handler):
        super(MyMotionDetector, self).__init__(camera)
        self.handler = handler
        self.first = True
        self.queue = np.full(20, False)

    def analyse(self, a) :
        a = np.sqrt(
            np.square(a['x'].astype(np.float)) +
            np.square(a['y'].astype(np.float))
        ).clip(0, 255).astype(np.uint8)
        if (a > 60).sum() > 50:
            # Ignore the first detection
            if self.first:
                self.first = False
                return
            self.queue[1:] = self.queue[:-1]
            self.queue[0] = True
            if np.all(self.queue):
                self.handler.motion_detected()

class CatDetector:
    def __init__(self):
        with picamera.PiCamera() as camera:
                camera.resolution = (1920, 1080)
                camera.framerate = 30
                stream = picamera.PiCameraCircularIO(camera, seconds=10)

                handler = CaptureHandler(camera, stream)

                print('Camera started')
                camera.start_recording(stream, format='h264',
                    motion_output=MyMotionDetector(camera, handler))

                while True:
                    handler.tick()
                    time.sleep(1)

                camera.stop_recording()