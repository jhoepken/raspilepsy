from time import sleep
from picamera import PiCamera

running = False

def online():
    """
    This function should only be used to get the status of the camera inside the
    templates and top-level code.
    """
    return running

class recorder:

    def __init__(self, target):

        self.target = target
        self.camera = PiCamera()
        self.audio = None

    def start(self):
        running = True
        self.camera = PiCamera()
        self.camera.start_recording(self.target)


    def stop(self):
        self.camera.stop_recording()

