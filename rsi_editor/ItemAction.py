from __future__ import annotations

import PySide2.QtCore as QtC
import PySide2.QtWidgets as QtW

from typing import Callable, List, Tuple

# Convenience class for actions which only work when their associated view has
# some item selected
class ItemAction(QtW.QAction):
    # This is really: indexTriggered = QtC.Signal(Union[QtC.QModelIndex, List[QtC.QModelIndex]])
    # But PySide2 doesn't like the annotation types
    indexTriggered = QtC.Signal(object)

    def __init__(self, text : str, view : QtW.QAbstractItemView):
        QtW.QAction.__init__(self, text, parent=view)
        self.view = view
        self.triggered.connect(lambda _checked: self.indexTrigger())

        self.checkValid = True
        self.allowMultiple = False
        self.enableCondition = (lambda _index: True)
        self.updateEnabled()
        self.view.modelChanged.connect(self.connectToCurrent)

    def setEnableIf(self, enableCondition : Callable[[QtC.QModelIndex], bool]) -> None:
        self.enableCondition = enableCondition
        self.updateEnabled()

    def setCheckValid(self, val : bool) -> None:
        self.checkValid = val
        self.updateEnabled()

    # If set to true, allow for the action to run when multiple indexes are
    # selected. The order in which the indexes are acted on is undefined.
    def setAllowMultiple(self, val : bool) -> None:
        self.allowMultiple = val
        self.updateEnabled()

    def connectToCurrent(self) -> None:
        if self.view.model() is not None:
            self.view.selectionModel().currentChanged.connect(lambda _newIndex, _oldIndex: self.updateEnabled())

    def updateEnabled(self) -> None:
        def checkIndex(index : QtC.QModelIndex) -> bool:
            return (not self.checkValid or index.isValid()) and self.enableCondition(index)

        if self.view.model() is None:
            self.setEnabled(False)

        selectionModel = self.view.selectionModel()

        if selectionModel is not None and selectionModel.hasSelection() \
            and len(selectionModel.selectedIndexes()) > 1:
            if self.allowMultiple:
                enabled = True

                for index in selectionModel.selectedIndexes():
                    enabled = enabled and checkIndex(index)

                self.setEnabled(enabled)
            else:
                self.setEnabled(False)
        else:
            currentIndex = self.view.currentIndex()
            self.setEnabled(checkIndex(currentIndex))

    def indexTrigger(self) -> None:
        assert self.view.model() is not None

        if self.allowMultiple:
            selectionModel = self.view.selectionModel()

            if selectionModel.hasSelection():
                self.indexTriggered.emit(selectionModel.selectedIndexes())
            else:
                self.indexTriggered.emit([self.view.currentIndex()])
        else:
            self.indexTriggered.emit(self.view.currentIndex())
