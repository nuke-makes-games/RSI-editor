import PySide2.QtCore as QtC
import PySide2.QtGui as QtG

import PIL as PIL # type: ignore
import PIL.ImageQt as PILQt # type: ignore

import rsi.state as RSIStatePy

# Typing imports
from .Rsi import Rsi
from typing import List, Optional, Tuple

# TODO: Have this be configured by zooming in and out
iconSize = QtC.QSize(100, 100)

# Wrapper class around an RSI state, for use in the editor
class State(QtC.QAbstractTableModel):
    delayChanged = QtC.Signal(QtC.QModelIndex, float)    

    def __init__(self, parentRsi : Rsi, stateName : str, parent : Optional[QtC.QObject] = None):
        QtC.QAbstractTableModel.__init__(self, parent)

        self.state = parentRsi.states[stateName]
        self.animations = [QtC.QSequentialAnimationGroup() for i in range(self.state.directions)]
        self.recalculateSummary()
        self.dataChanged.connect(self.frameDataChanged)
 
        self.rowsInserted.connect(lambda _parent, _first, _last: self.recalculateSummary())
        self.rowsRemoved.connect(lambda _parent, _first, _last: self.recalculateSummary())
        self.rowsMoved.connect(lambda _source, _first, _last, _dest, _destfirst: self.recalculateSummary())
        self.columnsInserted.connect(lambda _parent, _first, _last: self.recalculateSummary())
        self.columnsRemoved.connect(lambda _parent, _first, _last: self.recalculateSummary())
        self.columnsMoved.connect(lambda _source, _first, _last, _dest, _destfirst: self.recalculateSummary())

    # Getters

    def name(self) -> str:
        return self.state.name

    def directions(self) -> int:
        return self.state.directions

    # Convenience function - get pairs of images and delays for the given direction
    def frames(self, direction : int) -> List[Tuple[PIL.Image.Image, float]]:
        return list(zip(self.state.icons[direction], self.getDelays(direction)))

    def getDelays(self, direction : int) -> List[float]:
        if self.state.delays[direction] == []:
            return [0.0]
        else:
            return self.state.delays[direction]

    def delay(self, index: QtC.QModelIndex) -> Optional[float]:
        dirFrame = self.getDirFrame(index)

        if dirFrame is not None:
            direction, frame = dirFrame
            return self.state.delays[direction][frame]
        return None

    def setDelay(self, index : QtC.QModelIndex, delay : float) -> None:
        direction = index.row()
        frame = index.column() 
        
        leftMostChange = frame

        if len(self.state.delays[direction]) <= frame:
            leftMostChange = len(self.state.delays[direction])
            self.state.delays[direction].extend([0.0] * (frame - len(self.state.delays[direction]) + 1))

        self.state.delays[direction][frame] = delay

        self.dataChanged.emit(self.index(direction, leftMostChange), self.index(direction, frame), [QtC.Qt.DisplayRole])

    def frame(self, index : QtC.QModelIndex) -> Optional[PIL.Image.Image]:
        dirFrame = self.getDirFrame(index)

        if dirFrame is not None:
            (direction, frame) = dirFrame
            return self.state.icons[direction][frame]

        return None

    def setFrame(self, index : QtC.QModelIndex, image : PIL.Image.Image) -> None:
        direction = index.row()
        frame = index.column() 

        leftMostChange = frame

        if len(self.state.icons[direction]) <= frame:
            leftMostChange = len(self.state.icons[direction])
            self.state.icons[direction].extend([None] * (frame - len(self.state.icons[direction]) + 1))

        self.state.icons[direction][frame] = image.copy()

        self.dataChanged.emit(self.index(direction, leftMostChange), self.index(direction, frame), [QtC.Qt.DecorationRole])

    def getDirFrame(self, index : QtC.QModelIndex) -> Optional[Tuple[int, int]]:
        framesInDirection = self.frames(index.row())
        if index.column() >= len(framesInDirection):
            return None
        return (index.row(), index.column())

    # Frame manipulations

    def addFrame(self, index : QtC.QModelIndex, image : Optional[PIL.Image.Image] = None, delay : float = 0.0) -> None:
        if image is None:
            image = PIL.Image.new('RGBA', self.state.size)

        columnEnd = self.columnCount(QtC.QModelIndex()) - 1
        # In this case, we're going to insert a column
        insertColumn =  len(self.state.icons[index.row()]) == columnEnd

        if insertColumn:
            self.beginInsertColumns(QtC.QModelIndex(), columnEnd, columnEnd)

        self.state.icons[index.row()].insert(index.column(), image)
        self.state.delays[index.row()].insert(index.column(), delay)

        if insertColumn:
            self.endInsertColumns()
        
        self.dataChanged.emit(index, index.siblingAtColumn(self.columnCount(QtC.QModelIndex()) - 1))

    def deleteFrame(self, index : QtC.QModelIndex) -> Tuple[PIL.Image.Image, float]:
        removeColumn = True
        columnCount = self.columnCount(QtC.QModelIndex()) - 1
        for direction in range(self.directions()):
            if direction == index.row():
                continue

            # Remove the column if all other directions *DON'T* have a frame in it
            removeColumn = removeColumn and (len(self.state.icons[direction]) != columnCount)

        # If this is the case, removing this frame should delete the final column
        if removeColumn:
            self.beginRemoveColumns(QtC.QModelIndex(), columnCount - 1, columnCount - 1)

        image = self.state.icons[index.row()].pop(index.column())
        delay = self.state.delays[index.row()].pop(index.column())
        if removeColumn:
            self.endRemoveColumns()

        newColumnCount = self.columnCount(QtC.QModelIndex())
        if index.column() >= newColumnCount:
            self.dataChanged.emit(index, index.siblingAtColumn(newColumnCount - 1))

        return (image, delay) 

    # Direction manipulations

    ## Returns: ( <removed icon lists>, <removed delay lists> )
    def setDirections(self, directions : int) -> Tuple[List[List[PIL.Image.Image]], List[List[float]]]:
        if self.directions() == directions:
            return ([], [])

        if self.directions() > directions:
            firstRemoved = directions
            lastRemoved = self.directions() - 1

            self.beginRemoveRows(QtC.QModelIndex(), firstRemoved, lastRemoved)

            removedIcons = self.state.icons[firstRemoved:lastRemoved + 1]
            removedDelays = self.state.delays[firstRemoved:lastRemoved + 1]

            self.state.icons = self.state.icons[0:firstRemoved]
            self.state.delays = self.state.delays[0:firstRemoved]

            self.state.directions = directions

            self.endRemoveRows()

            return (removedIcons, removedDelays)
        else:
            firstInsertion = self.directions()
            lastInsertion = directions - 1

            self.beginInsertRows(QtC.QModelIndex(), firstInsertion, lastInsertion)


            # Basically, we extend the short list into the longer list by iterating
            # over the elements and copying each one until we have the size of list
            # we want
            dirIndex = 0

            for i in range(firstInsertion, directions):
                self.state.icons.insert(i, [ im.copy() for im in self.state.icons[dirIndex]])
                self.state.delays.insert(i, [ delay for delay in self.state.delays[dirIndex]])
                dirIndex = (dirIndex + 1) % (firstInsertion)

            self.state.directions = directions

            self.endInsertRows()

            return ([], [])

    # Model functions

    def rowCount(self, _parent : QtC.QModelIndex = QtC.QModelIndex()) -> int:
        return self.directions()

    def columnCount(self, _parent : QtC.QModelIndex = QtC.QModelIndex()) -> int:
        longestDirection = 0

        for i in range(self.directions()):
            longestDirection = max(longestDirection, len(self.state.icons[i]))

        return longestDirection + 1

    def index(self, row : int, column : int, parent : QtC.QModelIndex = QtC.QModelIndex()) -> QtC.QModelIndex:
        if column < self.columnCount(parent) and row < self.rowCount(parent):
            return self.createIndex(row, column)
        return QtC.QModelIndex()

    def data(self, index : QtC.QModelIndex, role : int = QtC.Qt.DisplayRole) -> object:
        dirFrame = self.getDirFrame(index)

        if dirFrame is not None:
            (direction, frame) = dirFrame
            frameInfo = self.frames(direction)[frame]
            
            if role == QtC.Qt.DisplayRole or role == QtC.Qt.EditRole:
                return frameInfo[1] # The delay
            if role == QtC.Qt.DecorationRole:
                image = frameInfo[0]

                framePixmap = QtG.QPixmap.fromImage(PILQt.ImageQt(image))
                framePixmap = framePixmap.scaled(iconSize)
                frameIcon = QtG.QIcon(framePixmap)

                return frameIcon

            return None
        else:
            if index.column() == self.summaryColumn():
                if role == QtC.Qt.DecorationRole:
                    # Some directions may have no animation
                    currentAnim = self.animations[index.row()]
                    if currentAnim is None:
                        return None

                    # and while the animation *should* never refer to the summary column
                    # it might do if data is fetched between the column being removed
                    # and the new animation being created
                    currentFrame = currentAnim.currentAnimation()
                    if currentFrame is not None and currentFrame.index.column() != self.summaryColumn():
                        return self.data(currentFrame.index, role)
                if role == QtC.Qt.DisplayRole:
                    return ''
            return None

    # TODO: Nice icons for directions
    def headerData(self, section : int, orientation : QtC.Qt.Orientation, role : int = QtC.Qt.DisplayRole) -> object:
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
            if section > self.columnCount(QtC.QModelIndex()):
                return None

            if role == QtC.Qt.DisplayRole:
                if section == self.summaryColumn():
                    return 'Animated'
                return f'Frame {section + 1}'
            return None

    def flags(self, index : QtC.QModelIndex) -> QtC.Qt.ItemFlags:
        if self.getDirFrame(index) is not None:
            return QtC.Qt.ItemIsSelectable | QtC.Qt.ItemIsEditable | QtC.Qt.ItemIsEnabled | QtC.Qt.ItemNeverHasChildren
        if index.column() == self.summaryColumn():
            return QtC.Qt.ItemNeverHasChildren | QtC.Qt.ItemIsEnabled
        return QtC.Qt.ItemNeverHasChildren

    def setData(self, index : QtC.QModelIndex, value : object, role : int = QtC.Qt.EditRole) -> bool:
        dirFrame = self.getDirFrame(index)

        if dirFrame is None:
            return False

        (direction, frame) = dirFrame

        if role == QtC.Qt.EditRole:
            if isinstance(value, str):
                try:
                    value = float(value)
                except ValueError:
                    return False

            if not isinstance(value, float):
                return False

            self.delayChanged.emit(index, value)
            return True
        return False

    def frameDataChanged(self, topLeft : QtC.QModelIndex, bottomRight : QtC.QModelIndex, roles : List[int] = list()) -> None:
        # Some data has changed - so we need to regenerate the
        # animations in the summary. First, we calculate which
        # rows are different now

        if (topLeft.column() < self.summaryColumn()):
            # +1, because these are inclusive and range is exclusive
            rowsChanged = range(topLeft.row(), bottomRight.row() + 1)

            self.recalculateSummary(rowsChanged)
    
    def summaryColumn(self) -> int:
        return self.columnCount(QtC.QModelIndex()) - 1

    def recalculateSummary(self, rowsChanged : Optional[range] = None) -> None:
        numRows = self.rowCount(QtC.QModelIndex())

        if rowsChanged is None:
            rowsChanged = range(numRows)

        numAnims = len(self.animations)
        if numAnims != numRows:
            if numAnims > numRows:
                self.animations = self.animations[0:numRows]
            else:
                self.animations = self.animations + ([QtC.QSequentialAnimationGroup()] * (numRows - numAnims))

        for rowIndex in rowsChanged:
            self.generateAnimation(rowIndex)

    def generateAnimation(self, row : int) -> None:
        animGroup = QtC.QSequentialAnimationGroup(parent=self)

        for column in range(self.columnCount(QtC.QModelIndex())):
            currentIndex = self.index(row, column)

            frameDelay = self.data(currentIndex, role=QtC.Qt.DisplayRole)
            if isinstance(frameDelay, float):
                animGroup.addAnimation(SummaryFrame(currentIndex, frameDelay, parent=self))
            else:
                break

        previousAnim = self.animations[row]
        if previousAnim is not None:
            previousAnim.stop()

        animIndex = self.index(row, self.summaryColumn(), QtC.QModelIndex())
        animGroup.currentAnimationChanged.connect(lambda _void: self.dataChanged.emit(animIndex, animIndex, [QtC.Qt.DecorationRole]))
        self.animations[row] = animGroup
        animGroup.setLoopCount(-1)
        animGroup.start()

# Special kind of animation that does nothing other than hold on to an index
# so that we can track it later
class SummaryFrame(QtC.QAbstractAnimation):
    def __init__(self, index : QtC.QModelIndex, delay : float, parent : QtC.QObject = None):
        QtC.QAbstractAnimation.__init__(self, parent)
        self.index = index
        self.delay = delay

    def duration(self) -> int:
        return int(self.delay * 1000)

    def updateCurrentTime(self, time : float) -> None:
        return
