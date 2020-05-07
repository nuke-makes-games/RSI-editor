import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

from .EditableLabel import EditableLabel
from .Icon import Icon

# What factor of icon size the icon labels are allowed to be
labelFactor = 1.2

# Icon with an editable label underneath and a double-click action
class LabelledIcon(QtW.QWidget):
    # Arguments in order:
    # - ID of this icon
    # - New label contents
    labelEdited = QtC.Signal(str, str)
    # Arguments in order:
    # - ID of this icon 
    drillDown = QtC.Signal(str)

    def __init__(self, ID, label, image, iconSize):
        QtW.QWidget.__init__(self)
        
        self.icon = Icon(ID, image, iconSize)
       
        # Throw up the drilldown directly
        self.icon.drillDown.connect(self.drillDown)
        
        self.label = EditableLabel(str(label))
        self.label.setMaximumWidth(self.icon.iconWidth * labelFactor)
        self.label.edited.connect(lambda old, new: self.labelEdited.emit(ID, new) if old != new else None)

        combinedLayout = QtW.QVBoxLayout()

        combinedLayout.addWidget(self.icon, alignment=QtC.Qt.AlignHCenter)
        combinedLayout.addWidget(self.label, alignment=QtC.Qt.AlignHCenter)

        combinedLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(combinedLayout)
