import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

import PIL as PIL
import PIL.ImageQt as PILQt

class StateIcon(QtW.QLabel):
    # Arguments in order:
    # - state name
    drillDown = QtC.Signal(str)

    def __init__(self, state, iconSize):
        QtW.QLabel.__init__(self)

        self.state = state

        if len(state.icons[0]) == 0:
            image = PIL.Image.new('RGB', self.currentRsi.size)
        else:
            image = state.icons[0][0]

        statePixmap = QtG.QPixmap.fromImage(PILQt.ImageQt(image))
        statePixmap = statePixmap.scaled(iconSize)

        QtW.QLabel.setPixmap(self, statePixmap)

        self.iconWidth = statePixmap.width()

    def mouseDoubleClickEvent(self, event):
        drillDown.emit(self.state.name)
