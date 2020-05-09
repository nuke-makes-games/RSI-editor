import PySide2.QtCore as QtC
import PySide2.QtGui as QtG

import PIL as PIL
import PIL.ImageQt as PILQt

import rsi

# Wrapper class around the RSI API, for use in the editor
class Rsi():
    # Constructors
    def __init__(self, rsi):
        self.rsi = rsi
        self.stateList = StateListModel(self)

    def fromFile(rsiPath):
        return Rsi(rsi.Rsi.open(rsiPath))

    def new(x, y):
        return Rsi(rsi.Rsi((x, y)))

    # Convenience function

    def save(self, path):
        self.rsi.write(path)
        return True

    # Getters

    def states(self):
        return self.rsi.states

    def size(self):
        return self.rsi.size

    def license(self):
        return self.rsi.license or ''

    def copyright(self):
        return self.rsi.copyright or ''

    # Setters - return True if the RSI is changed

    def setLicense(self, licenseText):
        if self.rsi.license != licenseText:
            self.rsi.license = licenseText
            return True
        return False

    def setCopyright(self, copyrightText):
        if self.rsi.copyright != copyrightText:
            self.rsi.copyright = copyrightText
            return True
        return False

    def renameState(self, oldStateName, newStateName):
        if oldStateName != newStateName:
            state = self.rsi.get_state(oldStateName)
            self.rsi.states.pop(oldStateName)
            state.name = newStateName
            self.rsi.set_state(state, newStateName)
            return True
        return False

class StateListModel(QtC.QAbstractListModel):
    def __init__(self, rsi, parent = None):
        QtC.QAbstractListModel.__init__(self, parent)

        self.size = rsi.size()
        self.states = list(rsi.states().values())

    def rowCount(self, _parent):
        return len(self.states)

    def getState(self, index):
        return self.states[index.row()]

    def data(self, index, role=QtC.Qt.DisplayRole):
        state = self.getState(index)

        if role == QtC.Qt.DisplayRole or role == QtC.Qt.EditRole:
            return state.name
        if role == QtC.Qt.DecorationRole:

            if len(state.icons[0]) == 0:
                image = PIL.Image.new('RGB', self.size)
            else:
                image = state.icons[0][0]

            stateImage = PILQt.ImageQt(image)
            stateIcon = QtG.QIcon(QtG.QPixmap.fromImage(stateImage))

            return stateIcon

    def flags(self, _index):
        # All states have the same flags
        return QtC.Qt.ItemIsSelectable | QtC.Qt.ItemIsEditable | QtC.Qt.ItemIsEnabled | QtC.Qt.ItemNeverHasChildren

    def setData(self, index, value, role=QtC.Qt.EditRole):
        state = self.getState(index)

        if not isinstance(value, str):
            return False

        state.name = value
        self.dataChanged.emit(index, index)
        return True

    # No header data right now

# Wrapper class around an RSI state, for use in the editor
class State():
    def __init__(self, parentRsi, stateName):
        self.state = parentRsi.states()[stateName]
        self.model = StateModel(self)

    # Getters

    def name(self):
        return self.state.name

    def directions(self):
        return self.state.directions

    # Convenience function - get pairs of images and delays for the given direction
    def frames(self, direction):
        return list(zip(self.state.icons[direction], self.state.delays[direction]))

    def setDelay(self, direction, frame, delay):
        self.state.delays[direction][frame] = delay

class StateModel(QtC.QAbstractTableModel):
    def __init__(self, state, parent = None):
        QtC.QAbstractTableModel.__init__(self, parent)

        self.state = state

    def rowCount(self, _parent):
        return self.state.directions()

    def columnCount(self, _parent):
        longestDirection = 0

        for i in range(self.state.directions()):
            longestDirection = max(longestDirection, len(self.state.frames(i)))

        return longestDirection

    def getDirFrame(self, index):
        framesInDirection = self.state.frames(index.row())
        if index.column() >= len(framesInDirection):
            return None
        return (index.row(), index.column())

    def data(self, index, role=QtC.Qt.DisplayRole):
        dirFrame = self.getDirFrame(index)

        if dirFrame is not None:
            (direction, frame) = dirFrame
            frameInfo = self.state.frames(direction)[frame]

            if role == QtC.Qt.DisplayRole or role == QtC.Qt.EditRole:
                return frameInfo[1] # The delay
            if role == QtC.Qt.DecorationRole:
                image = frameInfo[0]

                frameImage = PILQt.ImageQt(image)
                frameIcon = QtG.QIcon(QtG.QPixmap.fromImage(frameImage))

                return frameIcon
        else:
            return None

    # No header data yet...

    def flags(self, index):
        if self.getDirFrame(index) is not None:
            return QtC.Qt.ItemIsSelectable | QtC.Qt.ItemIsEditable | QtC.Qt.ItemIsEnabled | QtC.Qt.ItemNeverHasChildren
        return QtC.Qt.ItemNeverHasChildren

    def setData(self, index, value, role=QtC.Qt.EditRole):
        dirFrame = self.getDirFrame(index)

        if dirFrame is None:
            return

        (direction, frame) = dirFrame

        self.state.setDelay(direction, frame, value)
        self.dataChanged.emit(index, index)
        return True

