import numpy as np
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import matplotlib.pyplot as plt
##from scipy.signal import savgol_filter
import time
import cv2
from manipulator import Manipulator

class ImgSegmenter(Manipulator):
    ## Logging message signal
    message = pyqtSignal(str)  # Message signal
    ready = pyqtSignal()
    name = "ImageSegmenter"    
    ksize = 0 ## ksize - Median Blur aperture linear size; it must be odd and greater than 1, for example: 3, 5, 7 ...
    sizeFrac = 0.005 # Findgrid parameter as a fraction of the image size
    image = None
    ROIs = None
    
    def __init__(self, doPlot=False):
        super().__init__()
        self.doPlot = doPlot
        self.imgQuality = None
        self.procMillis = 0
        self.running = False
        if self.doPlot:
            self.fig, (self.ax1, self.ax2) = plt.subplots(2,1)
            self.graph1 = None
            self.graph2 = None
            self.ax1.grid(True)
            self.ax2.grid(True)
            plt.show(block=False)
        
    @pyqtSlot(np.ndarray)
    def start(self, image=None):
        try:
            if self.running == True:
                self.message.emit(self.name + ": Error, already running.")
            elif image is not None:
                self.message.emit(self.name + ": started.")
                self.startMillis = int(round(time.time() * 1000))
                self.image = image if self.ksize < 1 else cv2.medianBlur(image, self.ksize)  # blur the image, very slow
                # Find grid pattern along row and column averages
                row_av = cv2.reduce(self.image, 0, cv2.REDUCE_AVG, dtype=cv2.CV_32S).flatten('F')
                row_seg_list, row_mask, smooth_row_av = find1DGrid(row_av, int(self.sizeFrac*row_av.size))
                col_av = cv2.reduce(self.image, 1, cv2.REDUCE_AVG, dtype=cv2.CV_32S).flatten('F')
                col_seg_list, col_mask, smooth_col_av = find1DGrid(col_av, int(self.sizeFrac*col_av.size))
                # Compute metrics
                col_stuff = np.diff(smooth_col_av[~col_mask]) # slice masked areas
                col_stuff = col_stuff[25:-25]  # slice edge effects
                row_stuff = np.diff(smooth_row_av[~row_mask]) # slice masked areas
                row_stuff = row_stuff[25:-25]  # slice edge effects
                self.imgQuality = np.sqrt( np.var(col_stuff) # / col_stuff[np.abs(col_stuff) < .5].size
                                           + np.var(row_stuff) ) # / row_stuff[np.abs(row_stuff) < .5].size )
                # Rationale behind quality metrics: parameterize edge histogram by variance to amplitude (0-bin) ratio 
                # Plot curves
                if self.doPlot:
                    col_hist, bin_edges = np.histogram(col_stuff, bins=np.arange(-5,5,.1), density=True)
                    # Draw grid lines
                    self.ax1.clear()
                    self.graph1 = self.ax1.plot(row_stuff)[0]  # (col_hist)[0]
                    self.ax2.clear()
                    self.graph2 = self.ax2.plot(col_stuff)[0]  # smooth_col_av)[0]
### This way of plotting is probably faster, but right now can't get it to work with clearing as well                    
##                    if (self.graph1 is None):
##                        self.graph1 = self.ax1.plot(smooth_row_av)[0]
##                        self.graph2 = self.ax2.plot(smooth_col_av)[0]
##                    else: 
##                        self.graph1.set_image(np.arange(smooth_row_av.shape[1]), smooth_row_av)
##                        self.graph2.set_image(np.arange(smooth_col_av.shape[1]), smooth_col_av)
##                    # Need both of these in order to rescale
##                    self.ax1.relim()
##                    self.ax1.autoscale_view()
##                    self.ax2.relim()
##                    self.ax2.autoscale_view()
                    # We need to draw *and* flush
                    self.fig.canvas.draw()
                    self.fig.canvas.flush_events()
                # Create ROI list
                list_width = len(row_seg_list)
                list_length = len(col_seg_list)
                self.ROIs = np.zeros([list_width*list_length,4], dtype=np.uint16)
                ROI_area = 0
                for i, x in enumerate(row_seg_list):
                    for j, y in enumerate(col_seg_list):
                        self.ROIs[i+j*list_width] = [x[0],y[0],x[1],y[1]]
                        cv2.rectangle(self.image, (x[0],y[0]), (x[0]+x[1],y[0]+y[1]), (0, 255, 0), 2)
                        ROI_area += x[1]*y[1]
                self.imgQuality *= (ROI_area/np.prod(image.shape[0:2])) # Rationale: sharp edges result in ROI increase
### These deep copies are very inefficient, so omitted
##            # Mask the RoI and nonRoI areas
##                self.nonRoI = np.zeros(shape=self.RoI.shape, dtype=self.RoI.dtype)
##                self.nonRoI[:, ~row_mask] = self.RoI[:, ~row_mask] 
##                self.nonRoI[~col_mask, :] = self.RoI[~col_mask, :]
##            # Mask the grid, note that masking also acts as a trick to combine all border blobs
##                self.RoI[:, ~row_mask] = 0
##                self.RoI[~col_mask, :] = 0
##                self.RoIArea = cv2.countNonZero(self.RoI)
                self.procMillis = int(round(time.time() * 1000)) - self.startMillis
                self.message.emit(self.name + ": processing delay = " + str(self.procMillis) + " ms")
                self.running = False
                self.ready.emit()
        except Exception as err:
            self.message.emit("Error in " + self.name)
