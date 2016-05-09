import datetime
import imutils
from imutils.video.pivideostream import PiVideoStream
from imutils.video import FPS
import numpy as np
import time
import argparse
import cv2
import logging
from os import path

from django.core.management import BaseCommand

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

class Command(BaseCommand):

    help = """
    Server application for raspilepsy that takes care of continuous video
    surveillance, seizure/motion detection and video recording. Videos of
    seizures get stored automatically in database that is accessible via a
    Django webapp.  This server application serves only for the purpose of data
    aquisition and should be run via a cronjob. The users will not interact with
    it.
    """
    
    def add_arguments(self, parser):

        # Positional arguments

        # Named (optional) arguments
        parser.add_argument(
                "-r",
                "--resolution",
                default="640,480",
                type=pair,
                help="""
                Width and Height of video file. Default is 640 by 480 for real
                time analysis on RPi 3. The higher the resolution gets, the more
                demanding the computational requirements get in terms on real time
                processing. Full-HD is impossible to do on the RPi. Don't even think
                about it!
                Possible values are:
                320,240, 480x360, 640x480, 960x540, 1280x720(SD), 1920x1080(HD)
                
                (default: %(default)s)"""
                )
        parser.add_argument(
                "-f",
                "--framerate",
                type=int,
                default=10,
                help="""
                The framerate for the video cparser.ure and recording. Depending on
                the camera and resolution, this can vary. The lower the framerate, the
                larger the resource buffers are for real time video analysis. (default:
                %(default)s)"""
                )
        parser.add_argument(
                "--video",
                type=str,
                help="""
                Path to the video file, which is to be processed instead of a live
                video feed. (default: %(default)s)
                """
                )
        parser.add_argument(
                "-a",
                "--min-area",
                type=float,
                default=0.1,
                help="""
                Minimum area size that is recognized as something in motion.
                This is an absolute value and does *not* scale with the screen
                resolution! If you change the resolution, bear in mind to change this
                parameter accordingly. (default: %(default)s)
                """
                )
        parser.add_argument(
                "-b",
                "--motion-buffer",
                type=int,
                default=2,
                help="""
                Seconds to keep recording after no motion has been detected.
                This option is used to prevent the video recording from stopping as soon
                as no motion is detected by the algorithm, for a single frame. Which
                usually leads to a lot of very short and useless files that need to be
                deleted manually later on. It basically acts as a buffer. (default:
                %(default)s)
                """
                )
        parser.add_argument(
                "-d",
                "--delta-threshold",
                type=int,
                default=10,
                help="""
                The minimum absolute difference between the current frame and
                the averaged frame for a given pixel to be triggered as regarded as
                motion. Smaller threshold values lead to more motion to be detected,
                larger threshold values to less and hence to a stiffer system and a
                longer reaction time. (default: %(default)s)
                """
                )
        parser.add_argument(
                "-p",
                "--preview",
                dest='preview',
                action='store_true',
                help="""Opens the live preview window from opening. (Default)"""
                )
        parser.add_argument(
                "-n",
                "--no-preview",
                dest='preview',
                action='store_false',
                help="""Prevents the live preview window from opening."""
                )
        parser.add_argument(
                "--no-highlight",
                dest='noHighlight',
                action='store_true',
                help="""
                Prevents rectangles from been drawn around areas of motion. This
                speeds up the entire code and cleans up the video feed as well.
                (Default)
                """
                )
        parser.add_argument(
                "--highlight",
                dest='noHighlight',
                action='store_false',
                help="""
                Draws rectagles around areas that are detected as motion. This
                slows down the entire code and maybe messes up the video feed. Although
                it can be handy to be used in order to find the right parameter value
                for 'min-area' and '--delta-threshold' as well.
                """
                )
        parser.add_argument(
                "--dry-run",
                dest='dryRun',
                action='store_true',
                help="""Don't write any video files to disk."""
                )
        parser.add_argument(
                "--wet-run",
                dest='dryRun',
                action='store_false',
                help="""Write video files (Default)"""
                )
        parser.add_argument(
                "--downsampling",
                dest='downsampling',
                action='store_true',
                help="""Downsample video frames for realtime analysis"""
                )
        parser.add_argument(
                "--no-downsampling",
                dest='downsampling',
                action='store_false',
                help="""
                Don't downsample video frames fro realtime video analysis (Default)
                """
                )
        parser.add_argument(
                "--video-trigger",
                dest='videoTrigger',
                action='store_true',
                help="""Use video trigger to detect possible seizures (Default)."""
                )
        parser.add_argument(
                "--no-video-trigger",
                dest='videoTrigger',
                action='store_false',
                help="""Don't Use video trigger to detect possible seizures."""
                )

        parser.set_defaults(
                preview=True,
                noHighlight=True,
                dryRun=False,
                downsampling=False,
                videoTrigger=True
                )
    
    def handle(self, *args, **options):

        self.stdout.write("FOOBAR")
