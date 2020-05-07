import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

# A text label which supports double-click edit
class EditableLabel(QtW.QWidget):
    # Arguments in order:
    # - current label
    # - contents of edit box at end of editing
    edited = QtC.Signal(str, str)

    def __init__(self, label):
        QtW.QWidget.__init__(self)

        # Under the hood, this just switches between displaying a label and a
        # text entry, using this stacking widget.
        self.stack = QtW.QStackedWidget()

        self.label = QtW.QLabel(label)
        self.labelIndex = self.stack.addWidget(self.label)

        self.lineEdit = QtW.QLineEdit()
        self.lineEdit.editingFinished.connect(self.relabel)

        self.lineEditIndex = self.stack.addWidget(self.lineEdit)

        self.stack.setCurrentIndex(self.labelIndex)

        layout = QtW.QHBoxLayout()
        layout.addWidget(self.stack)
        # Make the bounding box invisible, otherwise this affects geometry
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def mouseDoubleClickEvent(self, event):
        if self.stack.currentIndex() != self.labelIndex:
            return

        self.stack.setCurrentIndex(self.lineEditIndex)
        self.lineEdit.setText(self.label.text())
        self.lineEdit.setFocus()

    @QtC.Slot()
    def relabel(self):
        self.edited.emit(self.label.text(), self.lineEdit.text())
        self.stack.setCurrentIndex(self.labelIndex)

