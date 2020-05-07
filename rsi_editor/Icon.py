import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

import PIL as PIL
import PIL.ImageQt as PILQt

class Icon(QtW.QLabel):
    # Arguments in order:
    # - state name
    drillDown = QtC.Signal(str)

    def __init__(self, ID, image, iconSize):
        QtW.QLabel.__init__(self)

        self.ID = ID

        pixmap = QtG.QPixmap.fromImage(PILQt.ImageQt(image))
        pixmap = pixmap.scaled(iconSize)

        QtW.QLabel.setPixmap(self, pixmap)

        self.iconWidth = pixmap.width()

    def mouseDoubleClickEvent(self, event):
        self.drillDown.emit(self.ID)
