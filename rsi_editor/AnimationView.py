import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

from .ItemAction import ItemAction
from .State import ImageRole

from typing import Optional

# Like a table, but does animation summaries
class AnimationView(QtW.QTableView):
    modelChanged = QtC.Signal()

    def __init__(self, parent : Optional[QtC.QObject] =None):
        QtW.QTableView.__init__(self, parent)

        self.setSortingEnabled(False)
        self.setGridStyle(QtC.Qt.NoPen)
        self.horizontalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeToContents)
        #self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setSectionResizeMode(QtW.QHeaderView.ResizeToContents)
        self.setContextMenuPolicy(QtC.Qt.ActionsContextMenu)

    def setModel(self, model : Optional[QtC.QAbstractItemModel]) -> None:
        QtW.QTableView.setModel(self, model)
        self.modelChanged.emit()

    def addItemAction(self, actionText : str) -> QtW.QAction:
        action = ItemAction(actionText, self)
        self.addAction(action)
        return action
