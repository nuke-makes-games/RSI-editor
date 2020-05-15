import PySide2.QtCore as QtC
import PySide2.QtWidgets as QtW

# Convenience class for actions which only work when their associated view has
# some item selected
class ItemAction(QtW.QAction):
    indexTriggered = QtC.Signal(QtC.QModelIndex)

    def __init__(self, text, view):
        QtW.QAction.__init__(self, text, parent=view)
        self.view = view
        self.triggered.connect(lambda _checked: self.indexTriggered.emit(self.view.currentIndex()))

        self.checkValid = True
        self.enableCondition = (lambda _index: True)
        self.updateEnabled(self.view.currentIndex())
        self.view.modelChanged.connect(self.connectToCurrent)

    def setEnableIf(self, enableCondition):
        self.enableCondition = enableCondition
        self.updateEnabled(self.view.currentIndex())

    def setCheckValid(self, val):
        self.checkValid = val
        self.updateEnabled(self.view.currentIndex())

    @QtC.Slot()
    def connectToCurrent(self):
        if self.view.model() is not None:
            self.view.selectionModel().currentChanged.connect(lambda newIndex, _oldIndex: self.updateEnabled(newIndex))

    @QtC.Slot()
    def updateEnabled(self, newViewIndex):
        if (not self.checkValid or newViewIndex.isValid()) and self.enableCondition(newViewIndex):
            self.setEnabled(True)
        else:
            self.setEnabled(False)
