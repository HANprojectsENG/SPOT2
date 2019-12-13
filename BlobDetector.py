"""@package docstring
Detect blobs in the image

TODO: how to pass roi's and imageQuality? via getter or (result) signal?
No median blurring, but bilateral?
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

class BlobDetector(Manipulator):
    """Object detector
        detects blobs

        \param image (the enhanced and segmented image)
        \return rects (the detected blobs in rectangles)"""
    
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
        """Image processing function."""        
        try:
            self.startTimer()                
            self.image = Image
            self.ROIs = ROIs
            self.imageQuality = None

            # Iterate ROis
            for ind, ROI in enumerate(ROIs):
                # slice image, assuming ROI:(left,top,width,height)
                ROI_image = self.image[ROI[1]:ROI[1]+ROI[3],ROI[0]:ROI[0]+ROI[2]]

                # Binarize and find blobs
                BWImage = cv2.adaptiveThreshold(ROI_image, 255,
                                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                self.invBin,
                                                self.blocksize,
                                                self.offset)

                # ConnectedComponentsWithStats output: number of labels, label matrix, stats(left,top,width,height), area
                blobFeatures = cv2.connectedComponentsWithStats(BWImage, 8, cv2.CV_32S)
                
                # Get blob RoI and area, and filter blobFeatures
                blobFeatures = blobFeatures[2][1:]  # skipping background (label 0)
                
                # Filter by blob area
                blobFeatures = blobFeatures[
                    np.where( (blobFeatures[:, cv2.CC_STAT_AREA] > self.minBlobArea) &
                              (blobFeatures[:, cv2.CC_STAT_AREA] < self.maxBlobArea) ) ]
                
                
                for blob in blobFeatures:
                    tl = (blob[0], blob[1])
                    br = (blob[0] + blob[2], blob[1] + blob[3])

                    # Compute some metrics of individual blobs
                    cv2.rectangle(ROI_image, tl, br, (0, 0, 0), 1)

                    # Mark blobs in image

# todo dit testen en afmaken


                    
##                    self.data = np.copy(tmpData[np.where(tmpData[:, 4] > self.minBlobArea)])
##                    self.data = self.data[np.where(self.data[:, 4] < self.maxBlobArea)]
##                # # filter ratio of Area vs ROI, to remove border blobs
##                # for index, row in enumerate(self.data):
##                #     if (row[2] * row[3]) / row[4] > 8:
##                #         print(row)
##                #         blobData = np.delete(blobData, (index), axis=0)
##                self.data = np.append(self.data, np.zeros(
##                    (self.data.shape[0], 3), dtype=int), axis=1)  # add empty columns

            # Plot last ROI
            if self.plot:
                cv2.imshow(self.name, BWImage)    
                    

##
##                # Compute some metrics of individual blobs
##                for row in self.data:
##                    tempImage = image[row[1]:row[1] + row[3], row[0]:row[0] + row[2]]
##                    tempBW = BWImage[row[1]:row[1] + row[3], row[0]:row[0] + row[2]]
##                    tempMask = tempBW > 0
##                    im2, contours, hierarchy = cv2.findContours(
##                        tempBW, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # assuming that there is one blob in an RoI, if not we need to fiddle with the label output matrix output[1]
##                    row[5] = int(cv2.Laplacian(tempImage, cv2.CV_64F).var())  # local image quality
##                    row[6] = len(contours[0])  # perimeter
##                    row[7] = int(np.mean(tempImage[tempMask]))  # foreground mean intensity

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
