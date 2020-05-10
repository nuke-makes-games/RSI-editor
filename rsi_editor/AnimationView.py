import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

import rsi

# Like a table, but does animation summaries
class AnimationView(QtW.QWidget):
    def __init__(self, parent=None):
        QtW.QWidget.__init__(self, parent)

        self.table = QtW.QTableView(parent=self)
        self.table.setSortingEnabled(False)
        self.table.setGridStyle(QtC.Qt.NoPen)
        
        self.setLayout(QtW.QHBoxLayout(parent=self))
        self.layout().addWidget(self.table)

    def setModel(self, model):
        animationModel = AnimationModel(model)
        self.table.setModel(animationModel)

    def model(self):
        return self.table.model().innerModel

# Wrapper model which also exposes animation summaries
class AnimationModel(QtW.QAbstractItemModel):
    def __init__(self, innerModel, parent = None):
        QtC.QAbstractItemModel.__init__(self, parent)

        self.innerModel = innerModel
        self.recalculateSummary()
        self.innerModel.dataChanged.connect(self.innerModelDataChanged)

    def innerModelDataChanged(self, topLeft, bottomRight, roles=list()):
        # Some data has changed - so we need to regenerate the
        # animations in the summary. First, we calculate which
        # rows are different now

        # +1, because these are inclusive and range is exclusive
        rowsChanged = range(topLeft.rows(), bottomRight.rows() + 1)

        self.recalculateSummary(rowsChanged)

    def recalculateSummary(rowsChanged=None):
        self.summaryColumn = self.columnCount(QtC.QModelIndex())
        
        # TODO
        #if rowsChanged is not None:

    def rowCount(self, _parent):
        return self.innerModel.rowCount()

    def columnCount(self, _parent):
        return self.innerModel.columnCount() + 1

    def data(self, index, role=QtC.Qt.DisplayRole):
        if index.column() == self.summaryColumn:
            if role == QtC.Qt.DecorationRole:
                # TODO

            return None
        else:
            return self.innerModel.data(index, role)

    def flags(self, index):
        if index.column() == self.summaryColumn:
            return QtC.Qt.ItemNeverHasChildren
        return self.innerModel.flags(index)

    def setData(self, index, value, role=QtC.Qt.EditRole):
        if index.column() == self.summaryColumn:
            return False

        return self.innerModel.setData(self, index, value, role)
