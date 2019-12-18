"""@package docstring
Documentation for this module.

"""
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import numpy as np
from PySide2.QtCore import *
import cv2
import inspect
import traceback
from objectSignals import ObjectSignals

class StatsComputer(QObject):
    '''
    More details.
    '''    

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.name = "compute statistics"
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
            y,x = np.histogram(self.blobs[:,4], bins=100, range=(self.minBlobArea,self.maxBlobArea))

            self.stats = y
                    
            # Finalize
            self.signals.result.emit(self.stats)  # Return the result of the processing

        except Exception as err:
            exc = traceback.format_exception(type(err), err, err.__traceback__, chain=False)
            self.signals.error.emit(exc)
            self.signals.message.emit('E: {} exception: {}'.format(self.name, err))
            
