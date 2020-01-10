"""@package docstring
Documentation for this module.
"""
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import numpy as np
from PySide2.QtCore import *
import inspect
import traceback
from objectSignals import ObjectSignals


class StatsComputer(QObject):
    '''
    More details.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.signals = ObjectSignals()

        # Blob area filtering parameters minBlobArea
        self.minBlobArea = kwargs['minBlobArea'] if 'minBlobArea' in kwargs else 10
        self.maxBlobArea = kwargs['maxBlobArea'] if 'maxBlobArea' in kwargs else 500

    def __del__(self):
        """The deconstructor."""
        None

    @Slot(np.ndarray)
    def update(self, blobs):
        try:
            self.startTimer()

            self.blobs = blobs

            # Compute statistics from blob ensemble parameters
            self.area_histogram, x = np.histogram(
                self.blobs[:, 4], bins=100, range=(self.minBlobArea, self.maxBlobArea))
            self.peri_to_area_histogram, x = np.histogram(
                np.divide(self.blobs[:, 4], self.blobs[:, 7]), bins=100)

        except Exception as err:
            exc = traceback.format_exception(
                type(err), err, err.__traceback__, chain=False)
            self.signals.error.emit(exc)
            self.signals.message.emit(
                'E: {} exception: {}'.format(__name__, err))
        finally:
            self.stopTimer()
            self.signals.finished.emit()  # Done

    def startTimer(self):
        """Start millisecond timer."""        
        self.startTime = int(round(time.time() * 1000))
        self.signals.message.emit('I: {} started'.format(__name__))            
        

    def stopTimer(self):
        """Stop millisecond timer."""        
        self.processsingTime = int(round(time.time() * 1000)) - self.startTime
        self.signals.message.emit('I: {} finished in {} ms'.format(__name__, self.processsingTime))
        