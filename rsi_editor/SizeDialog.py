import PySide2.QtCore as QtC
import PySide2.QtWidgets as QtW
import PySide2.QtGui as QtG

from typing import Optional

class SizeDialog(QtW.QDialog):
    def __init__(self, parent : QtC.QObject = None):
        QtW.QDialog.__init__(self, parent)

        overallLayout = QtW.QVBoxLayout()

        self.sizeInput = CombinedSpinBox()
        self.sizeInput.setX(32) # Sensible default

        self.lockedCheckbox = QtW.QCheckBox()
        self.lockedCheckbox.setText("Lock x/y values together")
        self.lockedCheckbox.stateChanged.connect(lambda _val: self.lockedChanged())
        self.lockedCheckbox.setChecked(True)

        buttonLayout = QtW.QHBoxLayout()

        cancelButton = QtW.QPushButton('Cancel')
        cancelButton.clicked.connect(lambda _checked: self.reject())
        cancelButton.setDefault(False)
        
        createButton = QtW.QPushButton('Create')
        createButton.clicked.connect(lambda _checked: self.accept())
        createButton.setDefault(True)

        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(createButton)

        buttonsWidget = QtW.QWidget()
        buttonsWidget.setLayout(buttonLayout)

        overallLayout.addWidget(self.sizeInput)
        overallLayout.addWidget(self.lockedCheckbox)
        overallLayout.addWidget(buttonsWidget)

        self.setLayout(overallLayout)
    
    def lockedChanged(self) -> None:
        self.sizeInput.setLocked(self.lockedCheckbox.isChecked())

    def size(self) -> Optional[QtC.QSize]:
        result = self.exec()

        if result == QtW.QDialog.Accepted:
            return self.sizeInput.size()
        else:
            return None

class CombinedSpinBox(QtW.QWidget):
    def __init__(self, parent : QtC.QObject = None):
        QtW.QWidget.__init__(self, parent)

        internalLayout = QtW.QHBoxLayout()

        self.xInput = QtW.QSpinBox(parent=self)
        self.xInput.setMaximum(256)
        self.xInput.valueChanged.connect(self.xChanged)

        self.yInput = QtW.QSpinBox(parent=self)
        self.yInput.setMaximum(256)

        internalLayout.addWidget(self.xInput)
        internalLayout.addWidget(self.yInput)

        self.setLayout(internalLayout)

        self.locked = False

    def setX(self, value : int) -> None:
        self.xInput.setValue(value)

    def setLocked(self, value : bool) -> None:
        self.locked = value

        if self.locked:
            self.yInput.setValue(self.xInput.value())
            self.yInput.setEnabled(False)
        else:
            self.yInput.setEnabled(True)

    def xChanged(self, val : int) -> None:
        if self.locked:
            self.yInput.setValue(val)

    def size(self) -> QtC.QSize:
        return QtC.QSize(self.xInput.value(), self.yInput.value())
