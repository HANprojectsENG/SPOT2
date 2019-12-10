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
from manipulator import Manipulator
import inspect
import traceback

class ImageEnhancer(Manipulator):
    """Image enhancer
    Subsequently, convert to grayscale, rotate and crop the image, 
    perform Contrast Limited Adaptive Histogram Equalization, gamma adaption.
     
    More details.
    """
    def __init__(self, Image, *args, **kwargs):
        """The constructor."""
        super().__init__('image enhancer', Image)

        # Deep copy
        self.image = Image.copy() if 'show' in kwargs else Image

        # Set crop area to (p1_y, p1_x, p2_y, p2_x)
        self.cropRect = kwargs['cropRect'] if 'cropRect' in kwargs else [0,0,0,0]

        # Set rotation angle, sometimes strange behaviour, and rounding seems required
        self.rotAngle = round(kwargs['rotAngle'], 1) if 'rotAngle' in kwargs else 0.0

        # Set threshold for contrast limiting
        self.clahe = cv2.createCLAHE(clipLimit=kwargs['clahe'], tileGridSize=(8,8)) if 'clahe' in kwargs else None

        # Set gamma correction
        self.gamma = kwargs['gamma'] if 'gamma' in kwargs else 1.0 
        
    def __del__(self):
        """The deconstructor."""
        None    
        
    def start(self):
        """Image processing function."""        
        try:
            self.startTimer()                
            self.signals.message.emit('I: {} started'.format(self.name))
            
            self.shape = self.image.shape
            
            # Convert to gray scale
            if len(self.shape) > 2:  # if color image
                self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

            # Rotate
            if 0.0 < abs(self.rotAngle) <= 5.0:
                image_center = tuple(np.array(self.image.shape[1::-1]) / 2)
                rot_mat = cv2.getRotationMatrix2D(image_center, self.rotAngle, 1.0) ## no scaling
                self.image = cv2.warpAffine(self.image, rot_mat, self.image.shape[1::-1], flags=cv2.INTER_LINEAR)
                deltaw = int(.5*np.round(np.arcsin(np.pi*np.abs(self.rotAngle)/180)*self.image.shape[0]))
                deltah = int(.5*np.round(np.arcsin(np.pi*np.abs(self.rotAngle)/180)*self.image.shape[1]))
            else:
                deltaw = deltah = 0

            # Crop
            p1_y = self.cropRect[0] + deltah
            p1_x = self.cropRect[1] + deltaw
            p2_y = self.cropRect[2] - deltah
            p2_x = self.cropRect[3] - deltaw
            if (p2_y > p1_y) and (p2_x > p1_x):
                self.image = self.image[p1_y:p2_y, p1_x:p2_x]
            
            # Contrast Limited Adaptive Histogram Equalization.
            if self.clahe is not None:  
                self.image = self.clahe.apply(image)
                
            # Change gamma
            if 1.0 < self.gamma < 10.0:  
                self.image = adjust_gamma(self.image, self.gamma)

            self.stopTimer()
            self.signals.message.emit('I: {} finished in {} ms'.format(self.name, self.processsingTime))
            self.signals.finished.emit()

                
        except Exception as err:
            exc = traceback.format_exception(type(err), err, err.__traceback__, chain=False)
            self.signals.error.emit(exc)
            self.signals.message.emit('E: {} exception: {}'.format(self.name, err))

        return self.image
