#!/usr/bin/python3
# -*- coding: utf-8 -*-
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import matplotlib.pyplot as plt
import time

## Autofocus
## Perform a grid search to optimize the image quality parameter, imgQual, by varying the camera focus.
## A grid of size P, centred around the current focus, with grid spacing dP is searched.
## When the maximum IQ is found, the focus is to the value where max IQ occured.
## Then, the procedure is repeated N_n times, where in every iteration the grid spacing is halved.
##
## TODO: extend to 2 dimensianol search by including optimization of the rotation angle

class AutoFocus(QObject):
##    Gridsearch of a hyperparameter H (image quality) over a process variable P (focus).
##    Start signal initiates a search around a given point P_centre, with gridsize N_p and gridspacing dP.
##    The search is repeated N_n times, where the gridspacing is halved with each step.
    message = pyqtSignal(str)  # Message signal
    VCValue = pyqtSignal(float)  # Focus signal
    ready = pyqtSignal()  # Autofocus done signal
    name = "AutoFocus"

    def __init__(self, doPlot=False):
        super().__init__()
        self.doPlot = doPlot
        self.k = 0 # plot position counter
        self.running = False
        
    @pyqtSlot(float)
    def start(self, P_centre=0, N_p=11, dP=1, N_n=10):
        if self.running == True:
            self.message.emit(self.name + ": Error, already running.")
        else:
            self.N_n = N_n  # Maximum number of iterations
            if (N_p & 1) != 1:  # Enforce N_p to be odd
                N_p += 1
                self.message.emit(self.name + "constructor warning : Grid size must be odd, so changed to " + str(N_p))
            self.N_p = N_p  # Grid size
            self.dP = dP  # Grid spacing, percentage change in VC current per step        
            self.H = np.zeros(shape=(self.N_p,1), dtype=float)
            self.P = np.zeros(shape=(self.N_p,1), dtype=float)
            self.P_centre = P_centre  # Set grid centre point
            self.n = 0  # First iteration
            self.p = 0  #
            self.p_sign = 1  # Process variable is rising
            if self.doPlot and (self.k == 0): # we have not plotted before
                self.k = 0 # plot position counter
                self.fig, (self.ax1, self.ax2) = plt.subplots(2,1)
                self.graph1 = None
                self.ax1.grid(True)
                self.ax1.set_ylabel("Image quality")
                self.graph2 = None
                self.ax2.grid(True)
                self.ax2.set_ylabel("Voice coil value")
                plt.show(block=False)        
            self.P[self.p] = self.P_centre-self.dP*int((self.N_p-1)/2)  # current process parameter
            self.VCValue.emit(self.P[self.p])  # Move to starting point of grid search
            self.message.emit(self.name + ": started.")
            self.running = True

    @pyqtSlot(float)
    def imgQualUpdate(self, imgQual=0):
        try:
            if self.running:  # autofocus is active
                self.message.emit(self.name + ": image quality updated.")
                self.H[self.p] = imgQual
                if self.doPlot:
               # draw grid lines
                    self.graph1 = self.ax1.plot(self.k, self.H[self.p], 'bo')[0]
                    self.graph2 = self.ax2.plot(self.k, self.P[self.p], 'bo')[0]
                # We need to draw *and* flush
                    self.fig.canvas.draw()
                    self.fig.canvas.flush_events()
                    self.k += 1
##                print(self.name + ": " + str(self.n) + ", " + str(self.p) + ", " + str(self.p_sign) + ": " + str(self.P_centre) + ": " +  str(self.P[self.p]) + ": " + str(self.H[self.p]))
                self.p += self.p_sign  # Move to next grid point
                if (0 <= self.p < self.N_p): # We're on the grid, so set parameter value
                    self.P[self.p] = self.P_centre + (self.dP/(self.n+1))*(self.p-int((self.N_p-1)/2))  # compute next grid point
                    value = self.P[self.p]
                else:
                    self.n += 1  # New iteration
                    self.P_centre = self.P[np.argmax(self.H),0] # set new grid centre point
                    if self.n < self.N_n:  # still iterating
##                        self.P.fill(0) # clear parameter array 
                        self.H.fill(0) # clear hyperparameter array 
                        self.p_sign *= -1 # Reverse direction
                        self.p += self.p_sign  # Reset current grid point
                        self.P[self.p] = self.P_centre + (self.dP/(self.n+1))*(self.p-int((self.N_p-1)/2))  # compute next grid point
                        value = self.P[self.p]
                    else:
                        self.running = False
                        value = self.P_centre
                self.message.emit(self.name + ": focus adapted to " + str(value))
                self.VCValue.emit(value)  # set next focus
        except Exception as err:
            self.message.emit(self.name + ": exception " + str(err))
            pass        
        
    @pyqtSlot()
    def stop(self):
        try:
            self.running = False
        except Exception as err:
            self.message.emit(self.name + ": exception " + str(err))

