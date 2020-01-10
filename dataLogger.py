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
import pandas as pd


class DataLogger(QObject):
    '''
    More details.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.signals = ObjectSignals()
        self.filename = None
        self.df = pd.DataFrame(
            columns = ['bb_left', 'bb_top', 'bb_width', 'bb_height',
                'cc_area', 'sharpness', 'SNR', 'perimeter'])

    def __del__(self):
        """The deconstructor."""
        None

    @Slot(np.ndarray)
    def update(self, blobs):
        try:
            self.startTimer()

            # self.df[len(self.df)]=blobs
            # self.df.to_csv(self.filename, index=False)

        except Exception as err:
            exc=traceback.format_exception(
                type(err), err, err.__traceback__, chain=False)
            self.signals.error.emit(exc)
            self.signals.message.emit(
                'E: {} exception: {}'.format(__name__, err))
        finally:
            self.stopTimer()
            self.signals.finished.emit()  # Done

    @Slot(str)
    def save(self, filename):
        print(self.df)
        self.df.to_csv(filename, index=False)

    def setFilename(self, filename):
        self.filename=filename

    def startTimer(self):
        """Start millisecond timer."""
        self.startTime=int(round(time.time() * 1000))
        self.signals.message.emit('I: {} started'.format(__name__))

    def stopTimer(self):
        """Stop millisecond timer."""
        self.processsingTime=int(round(time.time() * 1000)) - self.startTime
        self.signals.message.emit(
            'I: {} finished in {} ms'.format(__name__, self.processsingTime))
