"""@package docstring
Documentation for this module.
"""
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import numpy as np
from PySide2.QtCore import *
import cv2 as cv
import inspect
import traceback
from objectSignals import ObjectSignals

class StatsComputer(QObject):
    '''
    More details.
    '''    

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.stats = None
        self.signals = ObjectSignals()

        # Blob area filtering parameters minBlobArea
        self.minBlobArea = kwargs['minBlobArea'] if 'minBlobArea' in kwargs else 10
        self.maxBlobArea = kwargs['maxBlobArea'] if 'maxBlobArea' in kwargs else 500        

    def __del__(self):
        """The deconstructor."""
        None    

    def start(self, blobs):
        try:
            self.blobs = blobs

            # Compute statistics from blob ensemble parameters
            self.area_histogram, x = np.histogram(self.blobs[:,cv.CC_STAT_AREA], bins=100, range=(self.minBlobArea,self.maxBlobArea))
            self.peri_to_area_histogram, x = np.histogram(np.divide(self.blobs[:,cv.CC_STAT_AREA],self.blobs[:,7]), bins=100)
                    
            # Finalize
            self.signals.finished.emit()  # Return processing

        except Exception as err:
            exc = traceback.format_exception(type(err), err, err.__traceback__, chain=False)
            self.signals.error.emit(exc)
            self.signals.message.emit('E: {} exception: {}'.format(__name__, err))
            
