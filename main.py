import sys
from catdetector import CatDetector
from webstreamer import WebStreamer

is_setup = [arg for arg in sys.argv if arg == '--setup']
WebStreamer() if is_setup else CatDetector()
