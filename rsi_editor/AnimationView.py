import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

from .Rsi import ImageRole

# Like a table, but does animation summaries
class AnimationView(QtW.QWidget):
    edit = QtC.Signal(QtC.QModelIndex)

    def __init__(self, parent=None):
        QtW.QWidget.__init__(self, parent)

        self.table = QtW.QTableView(parent=self)
        self.table.setSortingEnabled(False)
        self.table.setGridStyle(QtC.Qt.NoPen)
        self.table.horizontalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeToContents)

        self.table.setContextMenuPolicy(QtC.Qt.ActionsContextMenu)

        layout = QtW.QHBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

        editorAction = QtW.QAction("Open in editor...", parent=self.table)
        editorAction.triggered.connect(lambda _checked: self.edit.emit(self.table.currentIndex()))
        
        self.table.addAction(editorAction)

    def model(self):
        return self.table.model()

    def setModel(self, model):
        animationModel = AnimationModel(model)
        self.table.setModel(animationModel)

    def reset(self):
        self.table.reset()

    def setIconSize(self, size):
        self.table.setIconSize(size)

# Wrapper model which also exposes animation summaries
class AnimationModel(QtC.QAbstractItemModel):
    def __init__(self, innerModel, parent = None):
        QtC.QAbstractItemModel.__init__(self, parent)

        self.innerModel = innerModel
        self.animations = []
        self.recalculateSummary()
        self.innerModel.dataChanged.connect(self.innerModelDataChanged)

    def innerModelDataChanged(self, topLeft, bottomRight, roles=list()):
        print("Something is happening")
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
                if section < self.summaryColumn:
                    return f'Frame {section + 1}'
                return 'Animated'
            return None


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
