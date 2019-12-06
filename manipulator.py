from abc import ABC, abstractmethod
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import time

class Manipulator(ABC):
    """Documentation for a class.
 
    More details.
    """    
    message = pyqtSignal(str)  # Message signal
    ready = pyqtSignal()
    processsingTime = 0 # processing time [ms]
    startTime = 0
    name = None    

    def __init__(Name, Image):
        self.name = Name
        self.image = Image
        super(Manipulator,self).__init__()
    
    @pyqtSlot()
    def show(self):
        pyqtShow()    

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
         
