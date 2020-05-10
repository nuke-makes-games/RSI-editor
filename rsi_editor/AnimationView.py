import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

# Like a table, but does animation summaries
class AnimationView(QtW.QWidget):
    def __init__(self, parent=None):
        QtW.QWidget.__init__(self, parent)

        self.table = QtW.QTableView(parent=self)
        self.table.setSortingEnabled(False)
        self.table.setGridStyle(QtC.Qt.NoPen)

        layout = QtW.QHBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def setModel(self, model):
        animationModel = AnimationModel(model)
        self.table.setModel(animationModel)

    def reset(self):
        self.table.reset()

# Wrapper model which also exposes animation summaries
class AnimationModel(QtC.QAbstractItemModel):
    def __init__(self, innerModel, parent = None):
        QtC.QAbstractItemModel.__init__(self, parent)

        self.innerModel = innerModel
        self.animations = []
        self.recalculateSummary()
        self.innerModel.dataChanged.connect(self.innerModelDataChanged)

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

            frameDelay = self.innerModel.data(currentIndex)
            if frameDelay is not None:
                animGroup.addAnimation(SummaryFrame(currentIndex, frameDelay, parent=self))
            else:
                break

        animIndex = self.createIndex(row, self.summaryColumn)
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

    def setData(self, index, value, role=QtC.Qt.EditRole):
        if index.column() == self.summaryColumn:
            return False

        result = self.innerModel.setData(index, value, role)

        if result:
            self.dataChanged.emit(index, index)
        return result

class SummaryFrame(QtC.QAbstractAnimation):
    def __init__(self, index, delay, parent=None):
        QtC.QAbstractAnimation.__init__(self, parent)
        self.index = index
        self.delay = delay

    def duration(self):
        return self.delay * 1000

    def updateCurrentTime(self, time):
        return
