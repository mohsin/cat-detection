import os
import time
import datetime
import picamera
import picamera.array
import numpy as np

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

    def tick(self):
        if self.detected:
            self.working = True
            self.detected = False
            print('Recording started')

            path = "captures/%s/" % datetime.datetime.now().date()

            os.makedirs(path, exist_ok = True)

            camera.split_recording(path + datetime.datetime.now().strftime("%H%M") + '-' + str(self.i) + '-' + 'motion.h264')
            while time.time() - self.last_detected < 5 or self.detected:
                camera.wait_recording(1)
            print('Recording complete')

            camera.split_recording(stream)
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