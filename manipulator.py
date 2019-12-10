from abc import ABC, abstractmethod
from PySide2.QtCore import *
from objectSignals import ObjectSignals
import time

class Manipulator(ABC):
    """Documentation for a class.
 
    More details.
    """      

    def __init__(self, Name, Image):
        """The constructor."""        
        super(Manipulator,self).__init__()
        self.name = Name
        self.show = False # Show intermediate results
        self.image = Image
        self.processsingTime = 0 # processing time [ms]
        self.startTime = 0
        self.signals = ObjectSignals()    
    
##    @Slot()
##    def show(self):
##        pyqtShow()    

    @abstractmethod
    def start(self):
        """Process image."""        
        pass

    def startTimer(self):
        """Start millisecond timer."""        
        self.startTime = int(round(time.time() * 1000))

    def stopTimer(self):
        """Stop millisecond timer."""        
        self.processsingTime = int(round(time.time() * 1000)) - self.startTime
         
