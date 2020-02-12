# import the necessary packages
from scipy.spatial import distance as dist
from objectSignals import *
from collections import OrderedDict
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import numpy as np
import time
import cv2
import traceback


class CentroidTracker(QThread):
    def __init__(self, *args, **kwargs):
        super().__init__()
        # initialize the next unique object ID along with two ordered
        # dictionaries used to keep track of mapping a given object
        # ID to its centroid and number of consecutive frames it has
        # been marked as "disappeared", respectively
        self.signals = ObjectSignals()
        self.nextObjectID = 0
        self.objects = OrderedDict()
        self.disappeared = list()
        self.euclideanDis = []
        #self.rects = []
        self.image = None
        self.startTime = 0
        self.Blobs = list()

        # store the number of maximum consecutive frames a given
        # object is allowed to be marked as "disappeared" until we
        # need to deregister the object from tracking
        self.maxDisappeared = 50

        self.imageShow = True

    def imageShowOff(self):
        if self.imageShow:
            self.imageShow = False

    def register(self, Blob):
        # when registering an object we use the next available object
        # ID to store the centroid
        self.objects[self.nextObjectID] = Blob
        self.objects[self.nextObjectID]._disappeared = 0
        self.nextObjectID += 1

    def deregister(self, objectID):
        # to deregister an object ID we delete the object ID from
        # both of our respective dictionaries
        del self.objects[objectID]
        if objectID in self.disappeared:
            self.disappeared.remove(objectID)

    def EuclideansReady(self):
        euclideans = []
        for i in self.euclideanDis:
            euclideans.extend(i)
        self.signals.resultDist.emit(euclideans)

    def showTrackedObjects(self):
        for (objectID, Blob) in self.objects.items():
            # draw both the ID of the object and the centroid of the
            # object on the output frame
            text = "ID {}".format(objectID)
            cv2.putText(
                self.image, text, (Blob._centroid[0]-10, Blob._centroid[1]-10),
                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.circle(self.image, (Blob._centroid[0], Blob._centroid[1]), 4, (0, 255, 0), -1)

        self.signals.result.emit(self.image)

    @Slot(np.ndarray)
    # Note that we need this wrapper around the Thread run function,
    # since the latter will not accept any parameters
    def update(self, image=None, Blobs=None):
        try:
            if self.isRunning():
                # thread is already running
                # drop frame
                self.signals.message.emit(
                    'I: {} busy, frame dropped'.format(__name__))
            elif Blobs is not None:
                # we have a new image
                self.image = image  # .copy()
                self.Blobs = Blobs
                self.start()

        except Exception as err:
            traceback.print_exc()
            self.signals.error.emit(
                (type(err), err.args, traceback.format_exc()))

    @Slot()
    def run(self):
        self.startTimer()
        self.signals.message.emit('I: Running worker "{}"\n'.format(__name__))

        distances = []

        # check to see if the list of Blobs is empty
        if len(self.Blobs) == 0:

            # loop over any existing tracked objects and mark them
            # as disappeared
            for objectID in self.disappeared:
                self.objects[objectID]._disappeared += 1

                # if we have reached a maximum number of consecutive
                # frames where a given object has been marked as
                # missing, deregister it
                if self.objects[objectID]._disappeared > self.maxDisappeared:
                    self.deregister(objectID)

            # return early as there are no centroids or tracking info
            # to update
            return self.objects

        # initialize an array of input centroids for the current frame
        # inputCentroids = np.zeros((len(self.Blobs), 2), dtype="int")
        # loop over the ROIs
        inputCentroids = []
        for Blob in self.Blobs:
            inputCentroids.append(Blob._centroid)

        # if we are currently not tracking any objects take the input
        # centroids and register each of them
        if len(self.objects) == 0:
            for Blob in self.Blobs :
                self.register(Blob)

        # otherwise, are are currently tracking objects so we need to
        # try to match the input centroids to existing object
        # centroids
        else:
            # grab the set of object IDs and corresponding centroids
            objectIDs = list(self.objects.keys())

            objectCentroids = []

            for Blob in self.objects.values():
                objectCentroids.append(Blob._centroid)

            # compute the distance between each pair of object
            # centroids and input centroids, respectively -- our
            # goal will be to match an input centroid to an existing
            # object centroid
            D = dist.cdist(np.array(objectCentroids), np.array(inputCentroids))

            # in order to perform this matching we must (1) find the
            # smallest value in each row and then (2) sort the row
            # indexes based on their minimum values so that the row
            # with the smallest value as at the *front* of the index
            # list
            rows = D.min(axis=1).argsort()

            # next, we perform a similar process on the columns by
            # finding the smallest value in each column and then
            # sorting using the previously computed row index list
            cols = D.argmin(axis=1)[rows]

            # in order to determine if we need to update, register,
            # or deregister an object we need to keep track of which
            # of the rows and column indexes we have already examined
            usedRows = set()
            usedCols = set()


            # loop over the combination of the (row, column) index
            # tuples
            for (row, col) in zip(rows, cols):
                # if we have already examined either the row or
                # column value before, ignore it
                # val
                if row in usedRows or col in usedCols:
                    continue

                # otherwise, grab the object ID for the current row,
                # set its new centroid, and reset the disappeared
                # counter
                objectID = objectIDs[row]
                self.objects[objectID]._centroid = inputCentroids[col]
                self.objects[objectID]._disappeared = 0
                if objectID in self.disappeared:
                    self.disappeared.remove(objectID)

                distances.append(D[row, col])

                # indicate that we have examined each of the row and
                # column indexes, respectively
                usedRows.add(row)
                usedCols.add(col)

            self.euclideanDis.append(distances)
            # compute both the row and column index we have NOT yet
            # examined
            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            # in the event that the number of object centroids is
            # equal or greater than the number of input centroids
            # we need to check and see if some of these objects have
            # potentially disappeared
            if D.shape[0] >= D.shape[1]:
                # loop over the unused row indexes
                for row in unusedRows:
                    # grab the object ID for the corresponding row
                    # index and increment the disappeared counter
                    objectID = objectIDs[row]
                    self.objects[objectID]._disappeared += 1

                    if objectID not in self.disappeared:
                        self.disappeared.append(objectID)

                    # check to see if the number of consecutive
                    # frames the object has been marked "disappeared"
                    # for warrants deregistering the object
                    if self.objects[objectID]._disappeared > self.maxDisappeared:
                        self.deregister(objectID)

            # otherwise, if the number of input centroids is greater
            # than the number of existing object centroids we need to
            # register each new input centroid as a trackable object
            else:
                for col in unusedCols:
                    self.register(self.Blobs[col])

        self.EuclideansReady()
        self.stopTimer()
        self.signals.finished.emit()

        # return the set of trackable objects
        return self.objects

    @Slot()
    def stop(self):
        if self.isRunning():
            self.signals.message.emit(
                'I: Stopping worker "{}"\n'.format(__name__))
            self.isStopped = True
            self.quit()

    def startTimer(self):
        """Start millisecond timer."""
        self.startTime = int(round(time.time() * 1000))
        self.signals.message.emit('I: {} started'.format(__name__))

    def stopTimer(self):
        """Stop millisecond timer."""

        self.processsingTime = int(round(time.time() * 1000)) - self.startTime
        self.signals.message.emit(
            'I: {} finished in {} ms'.format(__name__, self.processsingTime))
