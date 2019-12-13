"""@package docstring
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
from centroidtracker import CentroidTracker
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
tracker = CentroidTracker()

# Instantiate objects
if is_raspberry_pi():
    vs = PiVideoStream(resolution=(WIDTH, HEIGHT), monochrome=True, 
    framerate=FRAME_RATE, effect='blur', use_video_port=USE_VIDEO_PORT)
    pio = pigpio.pi()
    vc = VoiceCoil(pio)
    af = None
    heater = Heater(pio, 2000)
else:
    filename, _ = QFileDialog.getOpenFileName(caption='Open file', dir='.'
    , filter='*.mp4')
    print(filename)
    vs = VideoStream(filename, resolution=(WIDTH, HEIGHT), monochrome=True)

# Start video stream
vs.start(QThread.HighPriority)
processor.start(QThread.HighPriority)

# Connect video/image stream to processing (Qt.BlockingQueuedConnection or QueuedConnection?)
vs.signals.result.connect(processor.update, type=Qt.BlockingQueuedConnection)

# Connect GUI signals
window.rotateSpinBox.valueChanged.connect(processor.enhancer.setRotateAngle)
window.gammaSpinBox.valueChanged.connect(processor.enhancer.setGamma)
window.claheSpinBox.valueChanged.connect(processor.enhancer.setClaheClipLimit)
window.cropXp1Spinbox.valueChanged.connect(processor.enhancer.setCropXp1)
window.cropYp1Spinbox.valueChanged.connect(processor.enhancer.setCropYp1)
window.cropXp2Spinbox.valueChanged.connect(processor.enhancer.setCropXp2)
window.cropYp2Spinbox.valueChanged.connect(processor.enhancer.setCropYp2)
window.adaptiveThresholdOffsetSpinbox.valueChanged.connect(processor.detector.setOffset)
window.adaptiveThresholdBlocksizeSpinBox.valueChanged.connect(processor.detector.setBlockSize)
window.gridDetectorButton.stateChanged.connect(processor.setDetector)
if is_raspberry_pi():
    window.VCSpinBox.valueChanged.connect(vc.setVal)
    window.TemperatureSPinBox.valueChanged.connect(heater.setVal)

"""TODO:connect signals to the corresponding objects"""

# Connect GUI slots
vs.signals.message.connect(window.print_output)
vs.signals.error.connect(window.error_output)
processor.signals.message.connect(window.print_output)
processor.signals.error.connect(window.error_output)
processor.signals.result.connect(window.update)
##processor.signals.result.connect(
##    lambda x = str(processor.detector.blobs[0]) if not processor.detector.blobs is None else 0: window.print_output(x))


if is_raspberry_pi():
    af.signals.message.connect(window.print_output)
    af.signals.error.connect(window.error_output)
    vc.signals.message.connect(window.print_output)
    vc.signals.error.connect(window.error_output)
    heater.signals.message.connect(window.print_output)
    heater.signals.error.connect(window.error_output)
    
# Initialize objects from GUI
processor.enhancer.setRotateAngle(window.rotateSpinBox.value())
processor.enhancer.setGamma(window.gammaSpinBox.value())
processor.enhancer.setClaheClipLimit(window.claheSpinBox.value())
processor.enhancer.setCropXp1(window.cropXp1Spinbox.value())
processor.enhancer.setCropYp1(window.cropYp1Spinbox.value())
##processor.enhancer.setCropXp2(window.cropXp2Spinbox.value())
##processor.enhancer.setCropYp2(window.cropYp2Spinbox.value())
processor.detector.setOffset(window.adaptiveThresholdOffsetSpinbox.value())
processor.detector.setBlockSize(window.adaptiveThresholdBlocksizeSpinBox.value())

# Recipes invoked when mainWindow is closed, note that scheduler stops other threads
window.signals.finished.connect(processor.stop)
window.signals.finished.connect(vs.stop)
if is_raspberry_pi():
    window.signals.finished.connect(vc.stop)
    window.signals.finished.connect(autoFocus.stop)
    
# Start the show
window.show()
app.exec_()

    
    
