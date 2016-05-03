#!/usr/bin/python2.7
"""
Server application for raspilepsy that takes care of continuous video
surveillance, seizure/motion detection and video recording.
"""
import datetime
import imutils
import time
import argparse
import cv2
from os import path

__author__ = "Jens Hoepken"
__email__ = "jens@sourceflux.de"
__license__ = "GPL"
__maintainer__ = "Jens Hoepken"
__copyright__ = "Copyright 2016, sourceflux UG"

try:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except ImportError:
    pass

def pair(s):
    try:
        x,y = [int(sI) for sI in s.split(',')]
        return x,y
    except:
        raise argparse.ArgumentTypeError("Pair must be x,y")

ap = argparse.ArgumentParser(
        description = __doc__,
        epilog = """More information on how to run the server can be found on the
        project wiki https://bitbucket.org/jhoepken/raspilepsy/wiki/Home. Feel
        free to contribute in any way, either in testing, documentation,
        developing, feature ideas, bug reporting."""
        )
ap.add_argument(
        "-r",
        "--resolution",
        default="640,480",
        type=pair,
        help="""Width and Height of video file. Default is 640 by 480 for real
        time analysis on RPi 3. The higher the resolution gets, the more
        demanding the computational requirements get in terms on real time
        processing. Full-HD is impossible to do on the RPi. Don't even think
        about it!
        Possible values are:
        960x540, 1280x720(SD), 1920x1080(HD)
        """
        )
ap.add_argument(
        "-v",
        "--video",
        type=str,
        help="""Path to the video file, which is to be processed instead of a live
        video feed."""
        )
ap.add_argument(
        "-a",
        "--min-area",
        type=int,
        default=500,
        help="""Minimum area size that is recognized as something in motion.
        This is an absolute value and does *not* scale with the screen
        resolution! If you change the resolution, bear in mind to change this
        parameter accordingly."""
        )
ap.add_argument(
        "-b",
        "--motion-buffer",
        type=int,
        default=30,
        help="""Seconds to keep recording after no motion has been detected.
        This option is used to prevent the video recording from stopping as soon
        as no motion is detected by the algorithm, for a single frame. Which
        usually leads to a lot of very short and useless files that need to be
        deleted manually later on. It basically acts as a buffer."""
        )
ap.add_argument(
        "-p",
        "--no-preview",
        type=bool,
        default=False,
        help="""Prevents the live preview window from opening."""
        )
args = vars(ap.parse_args())

resolution = args["resolution"]

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

firstFrame = None

hasMotion = False
writer = None

# Read from live from camera
if args.get("video", None) is None:
    camera, rawCapture = initPiCamera()


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
    if args["no_preview"]:
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
