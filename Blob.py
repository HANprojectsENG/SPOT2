import numpy as np

class Blob():
	def __init__(self,x1, y1, x2, y2, centroid):
		self._x1 = x1
		self._x2 = x2
		self._y1 = y1
		self._y2 = y2
		self._centroid = centroid
		self._disappeared = 0
		self._local_sharpness = 0
		self._local_SNR = 0
		self._perimeter = 0	

	def __del__(self):
		None	

	def getTotalArea(self):
		return (x2-x1)*(y2-y1)

	def setCentroid(self, cX, cY):
		self._centroid = (cX, cY)

	def setBlobBox(self, x1, x2, y1, y2):
		#x1 = left x, x2 = right x
		#y1 = bottom y, y2 = top y
		self._x1 = x1
		self._x2 = x2
		self._y1 = y1
		self._y2 = y2

