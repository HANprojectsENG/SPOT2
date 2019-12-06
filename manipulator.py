from abc import ABC, abstractmethod
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

class Manipulator(ABC):

    message = pyqtSignal(str)  # Message signal
    ready = pyqtSignal()

    def __init__(Name, Image):
        self.name = Name
        self.image = Image
        super(Manipulator,self).__init__()
    
    
    def ready(self):
        pyqtSignal()
    
    def message(self,str):
        pyqtSignal(str)

    @abstractmethod
    def start(self):
        pass