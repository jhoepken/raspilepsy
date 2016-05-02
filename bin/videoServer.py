#!/usr/bin/python2.7
import datetime
import imutils
import time
import argparse
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera

resolution = (960, 540)

def initPiCamera():
    camera = PiCamera()
    camera.resolution = resolution
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=resolution)
    
    time.sleep(0.1)

    return (camera, rawCapture)

def highlightMotion(frame, avg):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    text = "No Seizure"
    
    # if the average frame is None, initialize it
    if avg is None:
        avg = gray.copy().astype("float")
        # rawCapture.truncate(0)
        # continue
 
    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

    # dilate the thresholded image to fill in holes, then find contours
    # on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)
    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE)

    cv2.imshow("gray", gray)
    cv2.imshow("thres", thresh)
    cv2.imshow("frameDelta", frameDelta)

    for c in cnts:
        if cv2.contourArea(c) < args["min_area"]:
            continue

        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Seizure"

    cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    return (frame, avg)

def annotateTime(frame):
    cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
    return frame

def hasMotion(frame):

    return True

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="Path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
args = vars(ap.parse_args())

# Read from live from camera
if args.get("video", None) is None:
    camera, rawCapture = initPiCamera()

firstFrame = None
# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # grab the raw NumPy array representing the image, then initialize the timestamp
    # and occupied/unoccupied text
    image = frame.array

    if hasMotion(image):
        (image, firstFrame) = highlightMotion(image, firstFrame)

    image = annotateTime(image)
    # show the frame
    cv2.imshow("Frame", image)
    key = cv2.waitKey(1) & 0xFF

    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break
