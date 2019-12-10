"""@package docstring
Image processor implements QThread
images are passed via wrapper
"""
 
#!/usr/bin/python3
# -*- coding: utf-8 -*-
from PySide2.QtCore import *
import numpy as np
import cv2
import traceback
from enhancer import ImgEnhancer
from ImgSegmentor import ImgSegmenter
from BlobDetector import BlobDetector
from objectSignals import ObjectSignals


class ImageProcessor(QThread):
    '''
    Worker thread

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.name = 'image processor'
        self.image = None
        self.signals = ObjectSignals()
        self.isStopped = False
        self.Enhancer = ImgEnhancer()
        self.Segmentor = ImgSegmenter()
        self.Detector = BlobDetector()

    def __del__(self):
        None
        self.wait()

    @Slot(np.ndarray)
    # Note that we need this wrapper around the Thread run function, since the latter will not accept any parameters
    def update(self, image=None): 
        try:
            self.enhancer = ImageEnhancer(image,
                                          cropRect = (0,0,image.shape[0],image.shape[1]),
                                          rotAngle = self.rotAngle)
            self.enhancer.signals.finished.connect(self.signals.finished.emit)
            self.enhancer.signals.message.connect(lambda message=str: self.signals.message.emit(message))
            self.enhancer.signals.error.connect(lambda err=tuple: self.signals.error.emit(err))
            
            # set cropping rectangle
##            self.enhancer.setCropRect((0,0,image.shape[0],image.shape[1]))

            if self.isRunning():  # thread is already running
                # drop frame
                self.signals.message.emit('I: {} busy, frame dropped'.format(self.name))
            elif image is not None:  # we have a new image
                self.image = image #.copy()
                self.start()
        except Exception as err:
            traceback.print_exc()
            self.signals.error.emit((type(err), err.args, traceback.format_exc()))

    # @Slot(float)
    # def setRotateAngle(self, val):
    #     try:
    #         if -5.0 <= val <= 5.0:
    #             self.rotAngle = round(val, 1)  # strange behaviour, and rounding seems required
    #         else:
    #             raise ValueError('rotation angle')
    #     except Exception as err:
    #         traceback.print_exc()
    #         self.signals.error.emit((type(err), err.args, traceback.format_exc()))      

    # @Slot(float)
    # def setGamma(self, val):
    #     if 0.0 <= val <= 10.0:
    #         self.gamma = val
        
    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        if not self.isStopped:
            
            self.signals.message.emit('Running worker "{}"\n'.format(self.name))
            
            # Retrieve args/kwargs here; and fire processing using them
            try:
                result = self.enhancer.start()
            except Exception as err:
                traceback.print_exc()
                self.signals.error.emit((type(err), err.args, traceback.format_exc()))
            else:
                self.signals.result.emit(result)  # Return the result of the processing
            finally:
                self.signals.finished.emit()  # Done

    @Slot()
    def stop(self):
        if self.isRunning():
            self.signals.message.emit('Stopping worker "{}"\n'.format(self.name))
            self.isStopped = True
            self.quit()
            

