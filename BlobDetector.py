import numpy as np
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import matplotlib.pyplot as plt
##from scipy.signal import savgol_filter
import time
import cv2
from manipulator import Manipulator

class BlobDetector(Manipulator):
    ## Logging message signal
    message = pyqtSignal(str)  # Message signal
    ## Image signal as numpy array
    ready = pyqtSignal()
    name = "BlobDetector"
    minBlobArea = 30
    maxBlobArea = 5000
    invertBinary = True # adaptiveThresholdInvertBinary
    showProcStep = 0
    image = None
    blobData = None

    def __init__(self, doPlot=False):
        super().__init__()
        self.doPlot = doPlot
        self.image = None
        self.procMillis = 0
        self.running = False
        self.offset = 0  # adaptiveThresholdOffset
        self.blocksize = 3  # adaptiveThresholdBlocksize
        if self.doPlot:
            cv2.namedWindow(self.name)
            plt.show(block=False)
            
    @pyqtSlot(np.ndarray)
    def start(self, image=None, ROIs=None):
        try:
            if self.running == True:
                self.message.emit(self.name + ": Error, already running.")
            elif (image is not None) and (ROIs is not None):
                self.message.emit(self.name + ": started.")
                self.startMillis = int(round(time.time() * 1000))
                self.image = image
                for ind, ROI in enumerate(ROIs):  # np.nditer(ROIs, flags=['multi_index']):
##                    print(str(ROI[0]) + ":"  + str(ROI[2]) + "," + str(ROI[1]) + ":"  + str(ROI[3]))
                    ROI_image = self.image[ROI[1]:ROI[1]+ROI[3],ROI[0]:ROI[0]+ROI[2]]  # slice image, assuming ROI:(left,top,width,height)
                    # Binarize and find blobs
                    BWImage = cv2.adaptiveThreshold(
                        ROI_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, self.invertBinary, self.blocksize, self.offset)
                    # ConnectedComponentsWithStats output: number of labels, label matrix, stats(left,top,width,height), area
                    blobFeatures = cv2.connectedComponentsWithStats(BWImage, 8, cv2.CV_32S)                
                    # Get blob RoI and area, and filter blobFeatures
                    blobFeatures = blobFeatures[2][1:]  # skipping background (label 0)
                    # Filter by blob area
                    blobFeatures = blobFeatures[np.where( (blobFeatures[:, 4] > self.minBlobArea) & (blobFeatures[:, 4] < self.maxBlobArea) )]
                    # Mark blobs in image
                    for blob in blobFeatures:
                        tl = (blob[0], blob[1])
                        br = (blob[0] + blob[2], blob[1] + blob[3])
                        cv2.rectangle(ROI_image, tl, br, (0, 0, 0), 1)

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

                # Plot ROI
                if self.doPlot:
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

                self.procMillis = int(round(time.time() * 1000)) - self.startMillis
                self.message.emit(self.name + ": processing delay = " + str(self.procMillis) + " ms")
                self.running = False                
                self.ready.emit()                
            
        except Exception as err:
            self.message.emit("Error in " + self.name)

    @pyqtSlot(float)
    def setOffset(self, val):
        if -10.0 <= val <= 10.0:
            self.offset = val
        else:
            self.message.emit("Error in " + self.name)

    @pyqtSlot(int)
    def setBlockSize(self, val):
        if (3 <= val <= 21) and (val & 1) == 1:
            self.blocksize = val
        else:
            self.message.emit("Error in " + self.name)


def adjust_gamma(image, gamma=1.0):
   invGamma = 1.0 / gamma
   table = np.array([((i / 255.0) ** invGamma) * 255
##   table = np.array([(  np.log(1.0 + i/255.0)*gamma) * 255  # log transform
      for i in np.arange(0, 256)]).astype("uint8")

   return cv2.LUT(image, table)
            
def rotateImage(image, angle):
    if angle != 0:
        image_center = tuple(np.array(image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0) ## no scaling
        result = cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
        return result
    else:
        return image

def moving_average(x, N=5):
    if N > 1 and (N & 1) == 1:
        x = np.pad(x, pad_width=(N // 2, N // 2),
                   mode='constant')  # Assuming N is odd
        cumsum = np.cumsum(np.insert(x, 0, 0))
        return (cumsum[N:] - cumsum[:-N]) / float(N)
    else:
        raise ValueError("Moving average size must be odd and greater than 1.")

def find1DGrid(data, N):    
    if N <= 1:
        raise ValueError('findGrid parameter <= 1')
    if (N & 1) != 1:  # enforce N to be odd
        N += 1
    gridSmoothKsize = N
    gridMinSegmentLength = 10*N    
    # high-pass filter, to suppress uneven illumination
    data = np.abs(data - moving_average(data, int(3*N)))
    data[:N] = 0 # cut off MA artifacts
    data[-N:] = 0 # cut off MA artifacts, why not -(N-1)/2?? ??
    smooth_data = moving_average(data, gridSmoothKsize)
    smooth_data = smooth_data - np.mean(smooth_data)
    mask_data = np.zeros(data.shape, dtype='bool')  # mask grid lines
    mask_data[np.where(smooth_data < 0)[0]] = True
    # Now filter mask_data based on segment length and suppress too short segments
    prev_x = False
    segmentLength = 0
    segmentList = []
    for index, x in enumerate(mask_data):
        if x:  # segment
            segmentLength += 1
        elif x != prev_x:  # falling edge
            if segmentLength < gridMinSegmentLength:  # suppress short segments
                mask_data[index - segmentLength: index] = False
                # print(diff(data[index - segmentLength:index]))
            else:
                segmentList.append((index - segmentLength, segmentLength))  # Save segment start and length
            segmentLength = 0  # reset counter
        prev_x = x
####    segmentList = np.array(segmentList)
####    # Rudimentary grid pattern recognition
####    # expected pattern: 2 groups of 2 segments (+/- 5%), where the largest is sqrt(2) larger than smallest
######    print(segmentList)
####    gridFound = False
####    if len(segmentList) >= 2 or len(segmentList) <= 10:  # Nr of segments should be reasonable
####        # try to separate short and long segments, knn wouldbe better
####        meanSegmentLength = np.mean(segmentList)
####        shortSegments = segmentList[np.where(segmentList < meanSegmentLength)]
####        longSegments = segmentList[np.where(segmentList > meanSegmentLength)]
####        nrOfSegmentsRatio = 0  # define a measure for nr of short vs nr long segments
####        if len(longSegments) > len(shortSegments):
####            nrOfSegmentsRatio = len(shortSegments) / len(longSegments)
####        elif len(shortSegments) > 0:
####            nrOfSegmentsRatio = len(longSegments) / len(shortSegments)
####
####        # nrOfSegmentsRatio = nrOfSegmentsRatio if nrOfSegmentsRatio <= 1.0 else 1 / nrOfSegmentsRatio
####        if nrOfSegmentsRatio > 0.5:  # nr of short and long segments should be approximaely equal
####            normSegmentLengthRatio = np.sqrt(2) * np.mean(shortSegments) / np.mean(longSegments)
####            if normSegmentLengthRatio >= .9 and normSegmentLengthRatio <= 1.1:
####                gridFound = True
####
    return (segmentList, mask_data, smooth_data)