import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

from .ItemAction import ItemAction
from .Rsi import ImageRole

# Like a table, but does animation summaries
class AnimationView(QtW.QTableView):
    modelChanged = QtC.Signal()

    def __init__(self, parent=None):
        QtW.QTableView.__init__(self, parent)

        self.setSortingEnabled(False)
        self.setGridStyle(QtC.Qt.NoPen)
        self.horizontalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeToContents)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeToContents)
        self.setContextMenuPolicy(QtC.Qt.ActionsContextMenu)

    def setModel(self, model):
        animationModel = AnimationModel(model)
        QtW.QTableView.setModel(self, animationModel)
        self.modelChanged.emit()

    def addItemAction(self, actionText):
        action = ItemAction(actionText, self)
        self.addAction(action)
        return action

# Wrapper model which also exposes animation summaries
class AnimationModel(QtC.QAbstractItemModel):
    def __init__(self, innerModel, parent = None):
        QtC.QAbstractItemModel.__init__(self, parent)

        self.innerModel = innerModel
        self.animations = []
        self.recalculateSummary()
        self.innerModel.dataChanged.connect(self.innerModelDataChanged)

        self.innerModel.dataChanged.connect(self.dataChanged.emit)
        self.innerModel.headerDataChanged.connect(self.headerDataChanged.emit)
        self.innerModel.layoutAboutToBeChanged.connect(self.layoutAboutToBeChanged.emit)
        self.innerModel.layoutChanged.connect(self.layoutChanged.emit)

        self.innerModel.rowsAboutToBeInserted.connect(self.beginInsertRows)
        self.innerModel.rowsInserted.connect(self.endInsertRows)
        self.innerModel.rowsAboutToBeMoved.connect(self.beginMoveRows)
        self.innerModel.rowsMoved.connect(self.endMoveRows)
        self.innerModel.rowsAboutToBeRemoved.connect(self.beginRemoveRows)
        self.innerModel.rowsRemoved.connect(self.endRemoveRows)

        self.innerModel.columnsAboutToBeInserted.connect(self.beginInsertColumns)
        self.innerModel.columnsInserted.connect(self.endInsertColumns)
        self.innerModel.columnsAboutToBeMoved.connect(self.beginMoveColumns)
        self.innerModel.columnsMoved.connect(self.endMoveColumns)
        self.innerModel.columnsAboutToBeRemoved.connect(self.beginRemoveColumns)
        self.innerModel.columnsRemoved.connect(self.endRemoveColumns)

    def innerModelDataChanged(self, topLeft, bottomRight, roles=list()):
        # Some data has changed - so we need to regenerate the
        # animations in the summary. First, we calculate which
        # rows are different now

        # +1, because these are inclusive and range is exclusive
        rowsChanged = range(topLeft.row(), bottomRight.row() + 1)

        self.recalculateSummary(rowsChanged)

    def recalculateSummary(self, rowsChanged=None):
        self.summaryColumn = self.columnCount(QtC.QModelIndex()) - 1
        
        numRows = self.rowCount(QtC.QModelIndex())

        if rowsChanged is None:
            rowsChanged = range(numRows)

        numAnims = len(self.animations)
        if numAnims != numRows:
            if numAnims > numRows:
                self.animations = self.animations[0..numRows]
            else:
                self.animations = self.animations + ([None] * (numRows - numAnims))

        for rowIndex in rowsChanged:
            self.generateAnimation(rowIndex)

    def generateAnimation(self, row):
        animGroup = QtC.QSequentialAnimationGroup(parent=self)

        for column in range(self.innerModel.columnCount(QtC.QModelIndex())):
            currentIndex = self.innerModel.index(row, column)

            frameDelay = self.innerModel.data(currentIndex, role=QtC.Qt.DisplayRole)
            if isinstance(frameDelay, float):
                animGroup.addAnimation(SummaryFrame(currentIndex, frameDelay, parent=self))
            else:
                break

        animIndex = self.index(row, self.summaryColumn, QtC.QModelIndex())
        animGroup.currentAnimationChanged.connect(lambda _void: self.dataChanged.emit(animIndex, animIndex, [QtC.Qt.DecorationRole]))
        self.animations[row] = animGroup
        animGroup.setLoopCount(-1)
        animGroup.start()

    def rowCount(self, _parent):
        return self.innerModel.rowCount(_parent)

    def columnCount(self, _parent):
        return self.innerModel.columnCount(_parent) + 1

    def index(self, row, column, _parent):
        if column <= self.summaryColumn and row < self.rowCount(_parent):
            return self.createIndex(row, column)
        return QtC.QModelIndex()

    def parent(self, _child):
        return QtC.QModelIndex()

    def data(self, index, role=QtC.Qt.DisplayRole):
        if index.column() == self.summaryColumn:
            if role == QtC.Qt.DecorationRole:
                currentFrame = self.animations[index.row()].currentAnimation()
                # Some directions may have no animation
                if currentFrame is not None:
                    return self.innerModel.data(currentFrame.index, role)
            if role == QtC.Qt.DisplayRole:
                return ''

            return None
        else:
            return self.innerModel.data(index, role)

    def flags(self, index):
        if index.column() == self.summaryColumn:
            return QtC.Qt.ItemNeverHasChildren | QtC.Qt.ItemIsEnabled
        return self.innerModel.flags(index)

    def headerData(self, section, orientation, role=QtC.Qt.DisplayRole):
        if orientation == QtC.Qt.Horizontal and section == self.summaryColumn and role == QtC.Qt.DisplayRole:
            return 'Animated'
        return self.innerModel.headerData(section, orientation, role)

    def setData(self, index, value, role=QtC.Qt.EditRole):
        if index.column() == self.summaryColumn:
            return False

        result = self.innerModel.setData(index, value, role)

        if result:
            self.dataChanged.emit(index, index)
        return result

    def frame(self, index):
        return self.data(index, role=ImageRole)

    def setFrame(self, index, image):
        return self.setData(index, image, role=ImageRole)

# Special kind of animation that does nothing other than hold on to an index
# so that we can track it later
class SummaryFrame(QtC.QAbstractAnimation):
    def __init__(self, index, delay, parent=None):
        QtC.QAbstractAnimation.__init__(self, parent)
        self.index = index
        self.delay = delay

    def duration(self):
        return self.delay * 1000

    def updateCurrentTime(self, time):
        return
