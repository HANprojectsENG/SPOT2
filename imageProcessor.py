"""@package docstring
Image processor implements QThread
images are passed via wrapper
"""
 
#!/usr/bin/python3
# -*- coding: utf-8 -*-
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import numpy as np
import cv2
import time
import traceback
from imageEnhancer import ImageEnhancer
from imageSegmenter import ImageSegmenter
from BlobDetector import BlobDetector
from objectSignals import ObjectSignals
from PySide2.QtCore import QThread
import time


class ImageProcessor(QThread):
    '''
    Worker thread

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self):
        super().__init__()

        self.image = None
        self.signals = ObjectSignals()
        self.isStopped = False
        self.enhancer = ImageEnhancer()
        self.segmenter = ImageSegmenter(plot=False)
        self.detector = BlobDetector(plot=False)
        self.gridDetection = False
       
        
    def __del__(self):
        None
        self.wait()

    @Slot(np.ndarray)
    # Note that we need this wrapper around the Thread run function, since the latter will not accept any parameters
    def update(self, image=None):
        try:
            
            if self.isRunning():
                # thread is already running
                # drop frame
                self.signals.message.emit('I: {} busy, frame dropped'.format(__name__))
            elif image is not None:
                # we have a new image
                self.image = image #.copy()        
                self.start(QThread.HighPriority)
                
        except Exception as err:
            traceback.print_exc()
            self.signals.error.emit((type(err), err.args, traceback.format_exc()))

       
    # @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        if not self.isStopped and self.image is not None:
            self.signals.message.emit('I: Running worker "{}"\n'.format(__name__))
           
            # Retrieve args/kwargs here; and fire processing using them
            try:
                self.startTimer()                

                # Enhance image
                self.image = self.enhancer.start(self.image)
                
                # Segment image according to grid 
                if self.gridDetection:
                    self.image = self.segmenter.start(self.image)
                    ROIs = self.segmenter.ROIs
                else:
                    ROIs = [[int(self.image.shape[1]/4), int(self.image.shape[0]/4),
                             int(self.image.shape[1]/2), int(self.image.shape[0]/2)]]

                # Blob detection
                result = self.detector.start(self.image, ROIs)

            except Exception as err:
                traceback.print_exc()
                self.signals.error.emit((type(err), err.args, traceback.format_exc()))
            else:
                self.signals.resultBlobs.emit(result,self.detector.blobs)
                self.signals.result.emit(result)  # Return the result of the processing
            finally:
                self.stopTimer()
                self.signals.finished.emit()  # Done
                
    @Slot()
    def stop(self):
        if self.isRunning():
            self.signals.message.emit('I: Stopping worker "{}"\n'.format(__name__))
            self.isStopped = True
            self.quit()

    @Slot(bool)
    def setDetector(self, val):
        self.gridDetection = val        


    def startTimer(self):
        """Start millisecond timer."""        
        self.startTime = int(round(time.time() * 1000))
        self.signals.message.emit('I: {} started'.format(__name__))            
        

    def stopTimer(self):
        """Stop millisecond timer."""        
        self.processsingTime = int(round(time.time() * 1000)) - self.startTime
        self.signals.message.emit('I: {} finished in {} ms'.format(__name__, self.processsingTime))        


            

