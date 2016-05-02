#!/usr/bin/python2.7
import datetime
import imutils
import time
import argparse
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera


def initPiCamera():
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=(640, 480))
    
    time.sleep(0.1)

    return (camera, rawCapture)

def highlightMotion():
    pass

def hasMotion():

    return True

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="Path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
args = vars(ap.parse_args())

# Read from live from camera
if args.get("video", None) is None:
    camera, rawCapture = initPiCamera()

# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # grab the raw NumPy array representing the image, then initialize the timestamp
    # and occupied/unoccupied text
    image = frame.array

    # show the frame
    cv2.imshow("Frame", image)
    key = cv2.waitKey(1) & 0xFF

    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break
