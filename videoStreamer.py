"""@package docstring
Documentation for this module.

TODO:
Auto-rotate, based on info obtained further down the DIP chain
Auto-crop, e.g. fixed, or based on rotate and on info obtained further down the DIP chain (cut uncharp edges)
 
"""

#!/usr/bin/python3
# -*- coding: utf-8 -*-

import numpy as np
from PySide2.QtCore import *
import cv2
from objectSignals import ObjectSignals

class VideoStream(QThread):
    """Video streamer
    stream frames from video file to np.ndarray PySide Signal
     
    More details.
    """    
    
    def __init__(self, Filename, *args, **kwargs):
        """
        The constructor. Filename should be specified.
        TODO: implement kwargs: resolution=(WIDTH, HEIGHT) and  monochrome=True
        """    
        super().__init__()
        
        self.name = "video stream"
        self.filename = Filename
        self.video = cv2.VideoCapture(self.filename)
        self.framecount = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.signals = ObjectSignals()
        self.isStopped = False
        
    def __del__(self):
        self.wait()

    @Slot()
    def run(self):
        '''
        Initialise the runner function.
        '''        
        self.signals.message.emit('Running worker "{}"\n'.format(self.name))
        
        try:
            for i in range(self.framecount):
                if self.isStopped:
                    break
                else:
                    # Read a new frame
                    ok, frame = self.video.read()
                    if ok:
                        self.signals.result.emit(frame)                    
        except Exception as err:
            traceback.print_exc()
            self.signals.error.emit((type(err), err.args, traceback.format_exc()))
        finally:
            self.signals.finished.emit()  # Done

    @Slot()
    def stop(self):
        if self.isRunning():
            self.signals.message.emit('Stopping worker "{}"\n'.format(self.name))
            self.isStopped = True
            self.quit()
