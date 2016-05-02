#!/usr/bin/python

import argparse
import cv2

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="Path to the video file")
args = vars(ap.parse_args())

# Read from live from camera
if args.get("video", None) is None:
    pass

# Read from file
else:
    camera = cv2.VideoCapture(args["video"])

# initialize the first frame in the video stream
firstFrame = None
