import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

class PixmapAnimation(QtC.QAbstractAnimation):
    def __init__(self, label, pixmap, duration):
        QtC.QAbstractAnimation.__init__(self, label)

        self.label = label
        self.pixmap = pixmap
        self._duration = duration

    def duration(self):
        return int(self._duration)

    def updateCurrentTime(self, currentTime):
        return True

    def updateDirection(self, direction):
        return True

    def updateState(self, newState, oldState):
        self.label.setPixmap(self.pixmap)
        return QtC.QAbstractAnimation.updateState(self, newState, oldState)
