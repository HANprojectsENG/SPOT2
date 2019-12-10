"""@package docstring
test
""" 
#!/usr/bin/python3
# -*- coding: utf-8 -*-
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
import numpy as np
import cv2
from mainWindow import MainWindow
from checkOS import is_raspberry_pi
from imageProcessor import ImageProcessor
# system dependent imports
if is_raspberry_pi():
    from pyqtpicam import PiVideoStream
    from autoFocis import AutoFocus
    from voiceCoil import VoiceCoil
    from heater import Heater
else:
    from videoStreamer import VideoStream
    
WIDTH = 640 # 3280 # 1648 # 1664 # 640 (1920 16:9)
HEIGHT = 480 # 2464 # 1232 # 928 # 480 (1088 16:9)

'''
main application
'''    
app = QApplication([])
window = MainWindow()
processor = ImageProcessor()

# Instantiate objects
if is_raspberry_pi():
    vs = PiVideoStream(resolution=(WIDTH, HEIGHT), monochrome=True, framerate=FRAME_RATE, effect='blur', use_video_port=USE_VIDEO_PORT)
else:
    filename, _ = QFileDialog.getOpenFileName(caption='Open file', dir='.', filter='*.mp4')
    print(filename)
    vs = VideoStream(filename, resolution=(WIDTH, HEIGHT), monochrome=True)

# Start video stream
vs.start()

# Connect video/image stream to processing (Qt.BlockingQueuedConnection or QueuedConnection?)
vs.signals.result.connect(processor.update, type=Qt.BlockingQueuedConnection)

# Connect GUI signals and slots
window.rotateSpinBox.valueChanged.connect(processor.setRotateAngle)
vs.signals.message.connect(window.print_output)
vs.signals.progress.connect(window.progress_fn)
vs.signals.error.connect(window.error_output)
##processor.signals.finished.connect(window.thread_complete)
processor.signals.message.connect(window.print_output)
processor.signals.result.connect(window.update)
processor.signals.error.connect(window.error_output)

window.signals.finished.connect(processor.stop)
window.signals.finished.connect(vs.stop)

window.show()

app.exec_()

