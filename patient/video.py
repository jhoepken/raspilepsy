from time import sleep
try:
    from picamera import PiCamera
except ImportError:
    pass

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
        try:
            self.camera = PiCamera()
        except:
            self.camera = None
        self.audio = None

    def start(self):
        running = True
        try:
            self.camera = PiCamera()
            self.camera.start_recording(self.target)
        except AttributeError:
            pass


    def stop(self):
        try:
            self.camera.stop_recording()
        except:
            pass

