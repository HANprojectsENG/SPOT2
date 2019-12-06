"""@package docstring
Documentation for this module.

TODO:
Auto-rotate, based on info obtained further down the DIP chain
Auto-crop, e.g. fixed, or based on rotate and on info obtained further down the DIP chain (cut uncharp edges)
 
"""
 
#!/usr/bin/python3
# -*- coding: utf-8 -*-

import numpy as np
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import cv2
import Manipulator

class ImgEnhancer(Manipulator):
    """Image enhancer
    Subsequently, convert to grayscale, crop the image, rotate (and crop again),
    perform Contrast Limited Adaptive Histogram Equalization, gamma adaption.
     
    More details.
    """
    image = None

    def __init__(self):
        """The constructor."""        
        super().__init__()
        self.cropRect = [0,0,0,0] # p1_y, p1_x, p2_y, p2_x
        self.rotAngle = 0.0
        self.gamma = 1.0                
        self.clahe = None
        
    def __del__(self):
        """The deconstructor."""
        None    
        
    def start(self):
        """Image processing function."""        
        try:
            if self.image is not None:
                self.startTimer()
                self.message.emit("Info: " + self.__name__ + ": started.")
                if len(self.image.shape) > 2:  # if color image
                    self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)  # convert to gray scale image
                self.image = self.image[self.cropRect[0]:self.cropRect[2], self.cropRect[1]:self.cropRect[3]] # crop the image
                if abs(self.rotAngle) > 0.0:
                    self.image = rotateImage(self.image, self.rotAngle)  # rotate
                    deltaw = int(.5*np.round(np.arcsin(np.pi*np.abs(self.rotAngle)/180)*self.image.shape[0]))
                    deltah = int(.5*np.round(np.arcsin(np.pi*np.abs(self.rotAngle)/180)*self.image.shape[1]))
                    self.image = self.image[+deltah:-deltah, +deltaw:-deltaw]  # autocrop when rotated
                if self.clahe is not None:
                    self.image = self.clahe.apply(self.image)  # Contrast Limited Adaptive Histogram Equalization.
                if self.gamma > 1.0:
                    self.image = adjust_gamma(self.image, self.gamma)  # change gamma
##                self.image = cv2.equalizeHist(self.image)  # histogram equalization
                self.stopTimer()
                self.message.emit("Info: " + self.__name__ + ": processing delay = " + str(self.processsingTime) + " ms")
                self.ready.emit()
        except Exception as err:
            self.message.emit("Error: " + self.__name__ + " " + str(err))
        
    @pyqtSlot(float)
    def setRotateAngle(self, angle):
        """ """        
        if -5.0 <= angle <= 5.0:
            self.rotAngle = round(angle, 1)  # strange behaviour, and rounding seems required
        else:
            self.message.emit("Error: " + self.__name__)
            
    @pyqtSlot(float)
    def setGamma(self, val):
        """ """        
        if 0.0 <= val <= 10.0:
            self.gamma = val
        else:
            self.message.emit("Error: " + self.__name__)

    @pyqtSlot(float)
    def setClaheClipLimit(self, val):
        """ """        
        if val <= 0.0:
            self.clahe = None
        elif val <= 10.0:
            self.clahe = cv2.createCLAHE(clipLimit=val, tileGridSize=(8,8))  # Sets threshold for contrast limiting
        else:
            self.message.emit("Error: " + self.__name__)

    @pyqtSlot(int)
    def setCropXp1(self, val):
        """ """        
        if 0 < val < self.cropRect[3]:        
            self.cropRect[1] = val
        else:
            self.message.emit("Error: " + self.__name__)

    @pyqtSlot(int)
    def setCropXp2(self, val):
        """ """        
        if self.cropRect[1] < val < self.image.shape[1]:            
            self.cropRect[3] = val
        else:
            self.message.emit("Error: " + self.__name__)

    @pyqtSlot(int)
    def setCropYp1(self, val):
        """ """        
        if 0 < val < self.cropRect[2]:        
            self.cropRect[0] = val            
        else:
            self.message.emit("Error: " + self.__name__)

    @pyqtSlot(int)
    def setCropYp2(self, val):
        """ """        
        if self.cropRect[0] < val < self.image.shape[0]:
            self.cropRect[2] = val            
        else:
            self.message.emit("Error: " + self.__name__)
