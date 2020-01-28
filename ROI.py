import numpy as np

class ROI():
	def __init__(self,x1, y1, x2, y2, label):
		self._label = label
		self._x1 = x1
		self._x2 = x2
		self._y1 = y1
		self._y2 = y2
		self._disappeared = 0

	def setCoordinates(self, x1, x2, y1, y2):
		self._x1 = x1
		self._x2 = x2
		self._y1 = y1
		self._y2 = y2

	def getTotalArea(self):
		return (x2-x1)*(y2-y1)

	def getCentroid(self):
		cX = int((x1 + (x1+x2)) /2.0)
		cY = int((Y1 + (Y1 + Y2))/ 2.0)
		return (cX, cY)

