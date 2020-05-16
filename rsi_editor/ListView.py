import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

from .ItemAction import ItemAction

from typing import Optional

# Convenience wrapper for QtW.QListView, adding some necessary signals
# and convenient methods
class ListView(QtW.QListView):
    modelChanged = QtC.Signal()

    def __init__(self, parent : Optional[QtC.QObject] =None):
        QtW.QListView.__init__(self, parent=parent)

    def setModel(self, model : Optional[QtC.QAbstractItemModel]) -> None:
        QtW.QListView.setModel(self, model)
        self.modelChanged.emit()

    def addItemAction(self, actionText : str) -> ItemAction:
        action = ItemAction(actionText, self)
        self.addAction(action)
        return action
