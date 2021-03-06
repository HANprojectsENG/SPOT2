"""@package docstring
Detect blobs in the image

TODO:
how to pass roi's and imageQuality? via getter or (result) signal?
Test and improve local blob snr

"""
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import numpy as np
from PySide2.QtCore import *
import cv2
import inspect
import traceback
from manipulator import Manipulator
import matplotlib.pyplot as plt
from Blob import Blob

class BlobDetector(Manipulator):
    """Object detector
        detects blobs

        \param image (the enhanced and segmented image)
        \return image (annotated)
    """
    
    def __init__(self, *args, **kwargs):
        """The constructor."""
        super().__init__("blob detector")

        # Blob area filtering parameters minBlobArea
        self.minBlobArea = kwargs['minBlobArea'] if 'minBlobArea' in kwargs else 10
        self.maxBlobArea = kwargs['maxBlobArea'] if 'maxBlobArea' in kwargs else 500

        # adaptiveThresholdInvertBinary
        self.invBin = kwargs['invBin'] if 'invBin' in kwargs else True

        # adaptiveThresholdOffset
        self.offset = kwargs['offset'] if 'offset' in kwargs else 0

        # adaptiveThresholdBlocksize
        self.blocksize = kwargs['blocksize'] if 'blocksize' in kwargs else 3  
        
        # Plotting
        self.plot = kwargs['plot'] if 'plot' in kwargs else False

        if self.plot:
            cv2.namedWindow(self.name)
            plt.show(block=False)

        """TODO: Add var rects -> detected blobs/rectangles"""       

        
    def __del__(self):
        """The deconstructor."""
        None    


    def start(self, Image, ROIs):
        """Image processing function.

        \param image (the enhanced and segmented image)
        \return image (the annotated image )

         local variable is the list of detected blobs with the following feature columns:
         [bb_left,bb_top,bb_width,bb_height, cc_area, sharpness, SNR]

         Sharpness is variation of the Laplacian (introduced by Pech-Pacheco
         "Diatom autofocusing in brightfield microscopy: a comparative study."

        """        
        try:
            self.startTimer()                
            self.image = Image
            self.ROIs = ROIs
            self._Blobs = list()

            # Iterate ROis
            for ROI in ROIs:
                # slice image, assuming ROI:(left,top,width,height)
                ROI_image = self.image[ROI[1]:ROI[1]+ROI[3],ROI[0]:ROI[0]+ROI[2]]

                # Binarize and find blobs
                BWImage = cv2.adaptiveThreshold(ROI_image, 255,
                                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                self.invBin,
                                                self.blocksize,
                                                self.offset)

                # ConnectedComponentsWithStats output: number of labels, label matrix, stats(left,top,width,height), area
                _,_,blobFeatures,_ = cv2.connectedComponentsWithStats(BWImage, 8, cv2.CV_32S)
                
                # Get blob RoI and area
                blobFeatures = blobFeatures[1:]  # skipping background (label 0)
                
                # Filter by blob area
                blobFeatures = blobFeatures[
                    np.where( (blobFeatures[:, cv2.CC_STAT_AREA] > self.minBlobArea) &
                              (blobFeatures[:, cv2.CC_STAT_AREA] < self.maxBlobArea) ) ]

                # Increase array size
                blobFeatures = np.concatenate([blobFeatures,
                                             np.zeros((blobFeatures.shape[0],3), dtype=int)],
                                            axis=1)

                # Annotate blobs and compute additional features

                for blob in blobFeatures:

                    tl = (blob[0], blob[1])
                    br = (blob[0] + blob[2], blob[1] + blob[3])
                    
                    # Compute some metrics of individual blobs
                    tempImage = self.image[tl[1]:br[1], tl[0]:br[0]]
                    I_0 = 255.0 - np.min(tempImage) # peak foreground intensity estimate
                    I_b = 255.0 - np.max(tempImage) # background intensity

                    # Shift coordinates wrt ROI
                    blob[0] += ROI[0]
                    blob[1] += ROI[1]

                    #centroid
                    cX = int((blob[0] + blob[0] +blob[2]) / 2.0)    # x1+x2 /2
                    cY = int((blob[1] - blob[3] + blob[1]) / 2.0)   # y1+y2 /2

                    DetectedBlob = Blob(blob[0], blob[0] + blob[2],
                        blob[1] - blob[3], blob[1], (cX,cY))

                    # Local sharpness column
                    DetectedBlob._local_sharpness = int(cv2.Laplacian(tempImage, cv2.CV_64F).var())

                    # Local SNR column
                    DetectedBlob._local_SNR = int((I_0-I_b)/np.sqrt(I_b)) if I_b>0 else 0

                    # Perimeter
                    tempBWImage = BWImage[tl[1]:br[1], tl[0]:br[0]]
                    contours, _ = cv2.findContours(tempBWImage, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
                    contour = max(contours, key=cv2.contourArea) # select largest contour
                    DetectedBlob._perimeter = len(contour)

                    #Add blob to list
                    self._Blobs.append(DetectedBlob)
                    
                    # Mark in image
                    # if self.plot:
                        # cv2.rectangle(ROI_image, tl, br, (0, 0, 0), 1)
                        #cv2.putText(ROI_image, str(blob[5]), br, cv2.FONT_HERSHEY_SIMPLEX, .5, (0,0,0), 1, cv2.LINE_AA)

            # Plot last ROI
            if self.plot:
                cv2.imshow(self.name, BWImage)    
                    
            # Finalize
            self.stopTimer()
            self.signals.finished.emit()                

        except Exception as err:
            exc = traceback.format_exception(type(err), err, err.__traceback__, chain=False)
            self.signals.error.emit(exc)
            self.signals.message.emit('E: {} exception: {}'.format(self.name, err))

        return self.image

    @Slot(float)
    def setOffset(self, val):
        if -10.0 <= val <= 10.0:
            self.offset = val
        else:
            raise ValueError('offset')

    @Slot(int)
    def setBlockSize(self, val):
        if (3 <= val <= 21) and (val & 1) == 1:
            self.blocksize = val
        else:
            raise ValueError('blocksize')
