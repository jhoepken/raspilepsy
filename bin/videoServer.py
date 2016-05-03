#!/usr/bin/python2.7
import datetime
import imutils
import time
import argparse
import cv2
from os import path
try:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except ImportError:
    pass

# resolution = (960, 540)
# resolution = (1920, 1080)
resolution = (1280, 720)
lastMotion = int(datetime.datetime.now().strftime("%s"))

def initPiCamera():
    camera = PiCamera()
    camera.resolution = resolution
    camera.framerate = 32
    rawCapture = PiRGBArray(camera, size=resolution)
    
    time.sleep(0.1)

    return (camera, rawCapture)

def highlightMotion(frame, avg, lastMotion):
    global args
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    text = "No Seizure"
    
    # if the average frame is None, initialize it
    if avg is None:
        avg = gray.copy().astype("float")
 
    # accumulate the weighted average between the current frame and
    # previous frames, then compute the difference between the current
    # frame and running average
    cv2.accumulateWeighted(gray, avg, 0.5)
    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

    thresh = cv2.threshold(frameDelta, args["motion_buffer"], 255, cv2.THRESH_BINARY)[1]

    # dilate the thresholded image to fill in holes, then find contours
    # on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)
    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        if cv2.contourArea(c) < args["min_area"]:
            continue

        # compute the bounding box for the contour, draw it on the frame,
        # and update the text
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
        text = "Seizure"

        lastMotion = int(datetime.datetime.now().strftime("%s"))

    cv2.putText(frame, "Status: {}".format(text), (10, 20),
    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    if int(datetime.datetime.now().strftime("%s")) - lastMotion > 5.0:
        hasMotion = False
    else:
        hasMotion = True

    return (frame, avg, hasMotion, lastMotion)

def annotateTime(frame):
    cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
    return frame

def initVideoFile(resolution):
    p = path.join(
                "/media",
                "jens",
                "windowsBackup",
                "raspilepsy",
                "footage_%s.avi"
                %(str(datetime.datetime.now().strftime("%Y-%M-%d_%H:%M:%S")))
                )
    print p
    writer = cv2.VideoWriter(p,
            cv2.cv.CV_FOURCC('M','J','P','G'),
            30,
            resolution,
            True)

    return writer

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="Path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
ap.add_argument("-b", "--motion-buffer", type=int, default=1, help="Minutes to keep recording after no motion has been detected")
args = vars(ap.parse_args())

# Read from live from camera
if args.get("video", None) is None:
    camera, rawCapture = initPiCamera()

firstFrame = None

hasMotion = False
writer = None


# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

    image = frame.array

    (image, firstFrame, hasMotion, lastMotion) = highlightMotion(image, firstFrame, lastMotion)
    image = annotateTime(image)
    
    try:
        if hasMotion:
            print "Writing image"
            writer.write(image)
        else:
            print "-> No recording demanded. Writer released and set to None!"
            writer.release()
            writer = None
    except:
        if hasMotion:
            print "Initialising new writer"
            writer = initVideoFile(resolution)
            writer.write(image)


    # show the frame
    cv2.imshow("Frame", image)
    key = cv2.waitKey(1) & 0xFF

    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)
    #cd $d
    #make
    #make install
    #cd ..


    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        try:
            writer.release()
        except:
            pass
        break
