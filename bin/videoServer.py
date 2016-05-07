#!/usr/bin/python2.7
"""
Server application for raspilepsy that takes care of continuous video
surveillance, seizure/motion detection and video recording. Videos of seizures
get stored automatically in database that is accessible via a Django webapp.
This server application serves only for the purpose of data aquisition and
should be run via a cronjob. The users will not interact with it.
"""
import datetime
import imutils
from imutils.video.pivideostream import PiVideoStream
from imutils.video import FPS
import time
import argparse
import cv2
import logging
from os import path

__author__ = "Jens Hoepken"
__email__ = "jens@sourceflux.de"
__license__ = "GPL"
__maintainer__ = "Jens Hoepken"
__copyright__ = "Copyright 2016, sourceflux UG"

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

try:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except ImportError:
    logging.critical('Cannot find picamera and caught ImportError')

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
        default="320,240",
        type=pair,
        help="""Width and Height of video file. Default is 640 by 480 for real
        time analysis on RPi 3. The higher the resolution gets, the more
        demanding the computational requirements get in terms on real time
        processing. Full-HD is impossible to do on the RPi. Don't even think
        about it!
        Possible values are:
        480x360, 640x480, 960x540, 1280x720(SD), 1920x1080(HD)
        
        (default: %(default)s)"""
        )
ap.add_argument(
        "-f",
        "--framerate",
        type=int,
        default=25,
        help="""The framerate for the video capture and recording. Depending on
        the camera and resolution, this can vary. (default: %(default)s)"""
        )
ap.add_argument(
        "-v",
        "--video",
        type=str,
        help="""Path to the video file, which is to be processed instead of a live
        video feed. (default: %(default)s)"""
        )
ap.add_argument(
        "-a",
        "--min-area",
        type=int,
        default=500,
        help="""Minimum area size that is recognized as something in motion.
        This is an absolute value and does *not* scale with the screen
        resolution! If you change the resolution, bear in mind to change this
        parameter accordingly. (default: %(default)s)"""
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
        deleted manually later on. It basically acts as a buffer. (default:
        %(default)s)"""
        )
ap.add_argument(
        "-d",
        "--delta-threshold",
        type=int,
        default=10,
        help="""The minimum absolute difference between the current frame and
        the averaged frame for a given pixel to be triggered as regarded as
        motion. Smaller threshold values lead to more motion to be detected,
        larger threshold values to less and hence to a stiffer system and a
        longer reaction time. (default: %(default)s)"""
        )
ap.add_argument(
        "-p",
        "--preview",
        dest='preview',
        action='store_true',
        help="""Opens the live preview window from opening. (Default)"""
        )
ap.add_argument(
        "-n",
        "--no-preview",
        dest='preview',
        action='store_false',
        help="""Prevents the live preview window from opening."""
        )
ap.add_argument(
        "--no-highlight",
        dest='noHighlight',
        action='store_true',
        help="""Prevents rectangles from been drawn around areas of motion. This
        speeds up the entire code and cleans up the video feed as well.
        (Default)"""
        )
ap.add_argument(
        "--highlight",
        dest='noHighlight',
        action='store_false',
        help="""Draws rectagles around areas that are detected as motion. This
        slows down the entire code and maybe messes up the video feed. Although
        it can be handy to be used in order to find the right parameter value
        for 'min-area' and '--delta-threshold' as well."""
        )
ap.add_argument(
        "--dry-run",
        dest='dryRun',
        action='store_true',
        help="""Don't write any video files to disk."""
        )
ap.add_argument(
        "--wet-run",
        dest='dryRun',
        action='store_false',
        help="""Write video files (Default)"""
        )

ap.set_defaults(
        preview=True,
        noHighlight=True,
        dryRun=False
        )

args = vars(ap.parse_args())

resolution = args["resolution"]
logging.debug("User selected resolution: %ix%i", resolution[0], resolution[1])
logging.debug("User selected framerate: %i fps", args["framerate"])
logging.debug("User selected min-area: %i ", args["min_area"])
logging.debug("User selected motion-buffer: %i s", args["motion_buffer"])
logging.debug("User selected delta_threshold: %i", args["delta_threshold"])
logging.debug("User selected dryRun: %r", args["dryRun"])
logging.debug("User selected noHighlight: %r", args["noHighlight"])
logging.debug("User selected preview: %r", args["preview"])

lastMotion = int(datetime.datetime.now().strftime("%s"))

def initPiCamera():
    logging.info("Initializing RPi Camera")
    global args
    camera = PiCamera()
    camera.resolution = resolution
    camera.framerate = args["framerate"]
    logging.debug("Done setting RPi Camera resolution and framerate")
    rawCapture = PiRGBArray(camera, size=resolution)
    
    logging.debug("Sleeping for a small fraction...")
    time.sleep(0.1)

    return (camera, rawCapture)

def annotateStatus(frame, status):
    """
    It is important that the frame is not assigned back to the input parameter,
    if it used for motion detection. Otherwise the changing text is detected as
    motion as well.
    """
    cv2.putText(
                frame,
                "Status: {}".format(status),
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2
            )
    return frame

def highlightMotion(frame, avg, lastMotion):
    """
    The live frame is scaled down to a width of 400px, in order to reduce the
    computational load on the RPi and comparable low CPU power platforms.
    Otherwise most of the frames will be dropped and the video feed looks like
    security feeds from the 1980s, which is rediculous.
    """
    global args

    smallFrame = imutils.resize(frame, width=300)
    gray = cv2.cvtColor(smallFrame, cv2.COLOR_BGR2GRAY)
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

    thresh = cv2.threshold(frameDelta, args["delta_threshold"], 255, cv2.THRESH_BINARY)[1]
    # dilate the thresholded image to fill in holes, then find contours
    # on thresholded image
    thresh = cv2.dilate(thresh, None, iterations=2)
    (cnts, _) = cv2.findContours(
                        thresh.copy(),
                        cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE
                    )

    if args["noHighlight"]:
        motionAreas = [cI for cI in cnts if cv2.contourArea(cI) < args["min_area"]]
        if len(motionAreas) == 0:
            text = "No Seizure"
        else:
            text = "Seizure"
            lastMotion = int(datetime.datetime.now().strftime("%s"))
    else:
        for c in cnts:
            if cv2.contourArea(c) < args["min_area"]:
                continue

            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
            text = "Seizure"

            lastMotion = int(datetime.datetime.now().strftime("%s"))

    annotateStatus(frame, text)

    if int(datetime.datetime.now().strftime("%s")) - lastMotion > args["motion_buffer"]:
        hasMotion = False
    else:
        hasMotion = True

    return (frame, avg, hasMotion, lastMotion)

def annotateTime(frame):
    """
    It is important that the frame is not assigned back to the input parameter,
    if it used for motion detection. Otherwise the changing time label is
    detected as motion as well.
    """
    cv2.putText(
                frame,
                datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (0, 0, 255),
                1
            )
    return frame

def initVideoFile(resolution):
    global args
    # TODO: Make this selectable via CLI
    p = path.join(
                "/home",
                "jens",
                "Desktop",
                "raspilepsy",
                "footage_%s.avi"
                %(str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
                )
    logging.info("Initializing video file at %s", p)

    # TODO: Select compression via CLI
    writer = cv2.VideoWriter(p,
            # cv2.cv.CV_FOURCC('M','J','P','G'),
            # cv2.cv.CV_FOURCC('P','I','M','1'),
            # cv2.cv.CV_FOURCC('X','2','6','4'),
            # cv2.cv.CV_FOURCC('M','P','4','V'),
            # XVID is UNCOMPRESSED!
            cv2.cv.CV_FOURCC('X','V','I','D'),
            args["framerate"],
            resolution,
            True)

    return writer

firstFrame = None

hasMotion = False
writer = None

# Read from live from camera
# if args.get("video", None) is None:
    # try:
        # camera, rawCapture = initPiCamera()
    # except NameError:
        # from sys import exit
        # exit()


vs = PiVideoStream(resolution=resolution,framerate=args["framerate"]).start()
time.sleep(2.0)
fps = FPS().start()
# capture frames from the camera
while True:
# for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    frame = vs.read()
    image = frame

    # TODO: Multiprocessing run this function on a different core
    (image, firstFrame, hasMotion, lastMotion) = highlightMotion(image, firstFrame, lastMotion)

    annotateTime(image)
    
    if not args["dryRun"]:
        try:
            if hasMotion:
                logging.info("Writing image to video file")
                # TODO: Multiprocessing write in parallel
                writer.write(image)
            else:
                logging.info("No recording demanded. Video file handler released.")
                writer.release()
                writer = None
        except:
            if hasMotion:
                writer = initVideoFile(resolution)
                # TODO: Multiprocessing write in parallel
                writer.write(image)


    # show the frame
    if args["preview"]:
        cv2.imshow("Frame", image)
    key = cv2.waitKey(1) & 0xFF

    # clear the stream in preparation for the next frame
    # rawCapture.truncate(0)

    fps.update()

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        try:
            writer.release()
        except:
            pass
        break
vs.stop()
