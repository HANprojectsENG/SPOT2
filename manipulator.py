from abc import ABC, abstractmethod
from PySide2.QtCore import *
from objectSignals import ObjectSignals
import time

class Manipulator(ABC):
    """Documentation for a class.
 
    More details.
    """      

    def __init__(self):
        """The constructor."""        
        super(Manipulator,self).__init__()
        self.image = None
        self.show = False # Show intermediate results
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
        self.signals.message.emit('I: {} started'.format(__name__))            
        

    def stopTimer(self):
        """Stop millisecond timer."""        
        self.processsingTime = int(round(time.time() * 1000)) - self.startTime
        self.signals.message.emit('I: {} finished in {} ms'.format(__name__, self.processsingTime))
        
         
