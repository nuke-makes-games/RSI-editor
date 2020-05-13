import PySide2.QtCore as QtC
import PySide2.QtGui as QtG

import PIL as PIL
import PIL.ImageQt as PILQt

import rsi as RSIPy

from collections import OrderedDict

# TODO: Have this be configured by zooming in and out
iconSize = QtC.QSize(100, 100)

# Custom view/model role - for getting and setting PIL Images
ImageRole = QtC.Qt.UserRole

# Wrapper class around the RSI API, for use in the editor
class Rsi(QtC.QAbstractListModel):
    stateRenamed = QtC.Signal(str, str)

    licenseChanged = QtC.Signal()
    copyrightChanged = QtC.Signal()

    # Constructors
    def __init__(self, rsi, parent=None):
        QtC.QAbstractListModel.__init__(self, parent)
        self.states = OrderedDict(rsi.states.items())
        self.size = rsi.size
        self.license = rsi.license
        self.copyright = rsi.copyright

    def fromFile(rsiPath):
        return Rsi(RSIPy.Rsi.open(rsiPath))

    def fromDmi(dmiPath):
        return Rsi(RSIPy.Rsi.from_dmi(dmiPath))

    def new(x, y):
        return Rsi(RSIPy.Rsi((x, y)))

    # Convenience function

    def save(self, path):
        rsi = RSIPy.Rsi(self.size)
        rsi.states = self.states
        rsi.license = self.license
        rsi.copyright = self.copyright
        rsi.write(path)
        return True

    # Setters - return True if the RSI is changed

    def setLicense(self, licenseText):
        if self.license != licenseText:
            self.license = licenseText
            self.licenseChanged.emit()
            return True
        return False

    def setCopyright(self, copyrightText):
        if self.copyright != copyrightText:
            self.copyright = copyrightText
            self.copyrightChanged.emit()
            return True
        return False

    def addState(self, stateName):
        if stateName in self.states:
            return False

        state = RSIPy.State(stateName, self.size, 1)

        currentFinalRow = self.rowCount(QtC.QModelIndex())

        self.beginInsertRows(QtC.QModelIndex(), currentFinalRow, currentFinalRow)
        self.states[stateName] = state
        self.endInsertRows()

        return True

    def addState(self, stateName, state):
        if not stateName in self.states:
            currentFinalRow = self.rowCount(QtC.QModelIndex())

            self.beginInsertRows(QtC.QModelIndex(), currentFinalRow, currentFinalRow)
            self.states[stateName] = state
            self.endInsertRows()
        else:
            self.states[stateName] = state
            currentIndex = self.getStateIndex(stateName)
            self.dataChanged.emit(currentIndex, currentIndex)
        return True

    def removeState(self, stateName):
        if not stateName in self.states:
            return None

        currentRow = self.getStateIndex(stateName).row()

        self.beginRemoveRows(QtC.QModelIndex(), currentRow, currentRow)
        state = self.states.pop(stateName)
        self.endRemoveRows()

        return state

    def renameState(self, oldStateName, newStateName):
        if not oldStateName in self.states:
            return False

        if oldStateName != newStateName:
            newRow = self.rowCount(QtC.QModelIndex()) - 1
            currentRow = self.getStateIndex(oldStateName).row()

            # If not the case, the row won't move, and endMoveRows() will actually
            # segfault
            if currentRow != newRow:
                self.beginMoveRows(QtC.QModelIndex(), currentRow, currentRow, QtC.QModelIndex(), newRow)

            state = self.states[oldStateName]
            self.states.pop(oldStateName)
            state.name = newStateName
            self.states[newStateName] = state

            if currentRow != newRow:
                self.endMoveRows()
            else:
                newIndex = self.getStateIndex(newStateName)
                self.dataChanged.emit(newIndex, newIndex)
            
            return True
        return False

    # Model methods

    def rowCount(self, _parent):
        return len(self.states)

    def getState(self, index):
        return list(self.states.values())[index.row()]

    def getStateIndex(self, stateName):
        for index, name in enumerate(self.states.keys()):
            if name == stateName:
                return self.createIndex(index, 0)
        return QtC.QModelIndex()

    def data(self, index, role=QtC.Qt.DisplayRole):
        state = self.getState(index)

        if role == QtC.Qt.DisplayRole or role == QtC.Qt.EditRole:
            return state.name
        if role == QtC.Qt.DecorationRole:

            if len(state.icons[0]) == 0:
                image = PIL.Image.new('RGB', self.size)
            else:
                image = state.icons[0][0]

            statePixmap = QtG.QPixmap.fromImage(PILQt.ImageQt(image))
            statePixmap = statePixmap.scaled(iconSize)
            stateIcon = QtG.QIcon(statePixmap)

            return stateIcon

    def flags(self, _index):
        # All states have the same flags
        return QtC.Qt.ItemIsSelectable | QtC.Qt.ItemIsEditable | QtC.Qt.ItemIsEnabled | QtC.Qt.ItemNeverHasChildren

    # setData is intercepted to produce something on the undo stack and also
    # fix other data
    def setData(self, index, value, role=QtC.Qt.EditRole):
        if role == QtC.Qt.EditRole:
            state = self.getState(index)

            if not isinstance(value, str):
                return False

            self.stateRenamed.emit(self.data(index, role=role), value)
            return True
        return False

    # No header data right now

# Wrapper class around an RSI state, for use in the editor
class State():
    def __init__(self, parentRsi, stateName):
        self.state = parentRsi.states[stateName]
        self.model = StateModel(self)

    # Getters

    def name(self):
        return self.state.name

    def directions(self):
        return self.state.directions

    # Convenience function - get pairs of images and delays for the given direction
    def frames(self, direction):
        return list(zip(self.state.icons[direction], self.getDelays(direction)))

    def getDelays(self, direction):
        if self.state.delays[direction] == []:
            return [None]
        else:
            return self.state.delays[direction]

    def setDelay(self, direction, frame, delay):
        # The only way this happens is if there is 1 frame
        if self.state.delays[direction] == []:
            self.state.delays[direction] = [delay]
        else:
            self.state.delays[direction][frame] = delay
        return True

    def setImage(self, direction, frame, image):
        self.state.icons[direction][frame] = image.copy()

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

                framePixmap = QtG.QPixmap.fromImage(PILQt.ImageQt(image))
                framePixmap = framePixmap.scaled(iconSize)
                frameIcon = QtG.QIcon(framePixmap)

                return frameIcon
            if role == ImageRole:
                return frameInfo[0]
        else:
            return None

    # TODO: Nice icons for directions
    def headerData(self, section, orientation, role=QtC.Qt.DisplayRole):
        if orientation == QtC.Qt.Vertical:
            if self.rowCount(QtC.QModelIndex()) == 1:
                if role == QtC.Qt.DisplayRole:
                    return 'All'
                return None
            else:
                if role == QtC.Qt.DisplayRole:
                    if section == 0:
                        return 'South'
                    if section == 1:
                        return 'North'
                    if section == 2:
                        return 'East'
                    if section == 3:
                        return 'West'
                    if section == 4:
                        return 'South East'
                    if section == 5:
                        return 'South West'
                    if section == 6:
                        return 'North East'
                    if section == 7:
                        return 'North West'
                return None
        else:
            if role == QtC.Qt.DisplayRole:
                return f'Frame {section + 1}'
            return None

    def flags(self, index):
        if self.getDirFrame(index) is not None:
            return QtC.Qt.ItemIsSelectable | QtC.Qt.ItemIsEditable | QtC.Qt.ItemIsEnabled | QtC.Qt.ItemNeverHasChildren
        return QtC.Qt.ItemNeverHasChildren

    def setData(self, index, value, role=QtC.Qt.EditRole):
        dirFrame = self.getDirFrame(index)

        if dirFrame is None:
            return

        (direction, frame) = dirFrame

        if role == QtC.Qt.EditRole:
            if isinstance(value, str):
                try:
                    value = float(value)
                except ValueError:
                    return False

            if self.state.setDelay(direction, frame, value):
                self.dataChanged.emit(index, index)
                return True
            return False

        if role == ImageRole:
            self.state.setImage(direction, frame, value)
            self.dataChanged.emit(index, index)
            return True

        return False

