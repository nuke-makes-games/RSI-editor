import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

from rsi import Rsi

from .EditableLabel import EditableLabel
from .FlowLayout import FlowLayout
from .Icon import Icon 

rsiFileFilter = 'Robust Station Image (*.rsi);;RSI JSON metadata (*.json)'

# TODO: Have this be configured by zooming in and out
iconSize = QtC.QSize(50, 50)
# What factor of icon size the state names are allowed to be
stateNameFactor = 1.2

class CurrentRsi():
    def __init__(self, rsi, path):
        self.rsi = rsi
        self.path = path
        self.dirty = False

    def close(self):
        if self.dirty:
            return False

        return True

    def save(self):
        if not self.hasPath():
            return False

        self.rsi.write(self.path)
        self.dirty = False
        return True

    def states(self):
        return self.rsi.states

    def size(self):
        return self.rsi.size

    def license(self):
        return self.rsi.license or ''

    def copyright(self):
        return self.rsi.copyright or ''

    def hasPath(self):
        return self.path is not None and self.path != ''

    def setPath(self, path):
        self.path = path

    @QtC.Slot()
    def updateLicense(self, licenseText):
        if self.rsi.license != licenseText:
            self.rsi.license = licenseText
            self.dirty = True

    @QtC.Slot()
    def updateCopyright(self, copyrightText):
        if self.rsi.copyright != copyrightText:
            self.rsi.copyright = copyrightText
            self.dirty = True

    def renameState(self, oldStateName, newStateName):
        state = self.rsi.get_state(oldStateName)
        self.rsi.states.pop(oldStateName)
        state.name = newStateName
        self.rsi.set_state(state, newStateName)
        self.dirty = True

class CurrentState():
    def __init__(self, parentRsi, stateName):
        self.parentRsi = parentRsi
        self.state = self.parentRsi.states()[stateName]

    def name(self):
        return self.state.name

    def directions(self):
        return self.state.directions

    def frames(self, direction):
        return zip(self.state.icons[direction], self.state.delays[direction])

class EditorWindow(QtW.QMainWindow):
    def __init__(self):
        QtW.QMainWindow.__init__(self)
        self.setWindowTitle("RSI editor")
        self.editorMenu()

        self.currentRsi = None
        self.currentState = None
        self.reloadRsi()


    def editorMenu(self):
        fileMenu = self.menuBar().addMenu("&File")

        newAction = fileMenu.addAction("&New")
        openAction = fileMenu.addAction("&Open")
        saveAction = fileMenu.addAction("&Save")
        fileMenu.addSeparator()
        preferencesAction = fileMenu.addAction("Preferences")

        # Set up new RSI
        newAction.setShortcut(QtG.QKeySequence.New)
        newAction.triggered.connect(self.newRsi)

        # Set up file opening
        openAction.setShortcut(QtG.QKeySequence.Open)
        openAction.triggered.connect(self.openRsi)

        # Set up file saving
        saveAction.setShortcut(QtG.QKeySequence.Save)
        saveAction.triggered.connect(self.saveRsi)

        # Set up preferences
        preferencesAction.setShortcut(QtG.QKeySequence.Preferences)

    def reloadRsi(self):
        if self.currentRsi is None:
            return

        splitter = QtW.QSplitter()
        splitter.setOrientation(QtC.Qt.Vertical)

        if self.currentState is not None:
            stateContentsGroupBox = QtW.QGroupBox(self.currentState.name())
            stateContentsGrid = QtW.QGridLayout()

            for direction in range(self.currentState.directions()):
                frameNumber = 0
                for (image, delay) in self.currentState.frames(direction):
                    frameID = f'{self.currentState.name()}_{direction}_{frameNumber}'
                    frameIcon = Icon(frameID, image, iconSize)
                    #TODO: Editing the frame!
                    #stateIcon.drillDown.connect(self.openState)
            
                    delayLabel = EditableLabel(str(delay))
                    delayLabel.setMaximumWidth(frameIcon.iconWidth * stateNameFactor)
                    #TODO: Changing the delay
                    #delayLabel.edited.connect

                    frameCombinedLayout = QtW.QVBoxLayout()

                    frameCombinedLayout.addWidget(frameIcon, alignment=QtC.Qt.AlignHCenter)
                    frameCombinedLayout.addWidget(delayLabel, alignment=QtC.Qt.AlignHCenter)

                    frameCombined = QtW.QWidget()
                    frameCombined.setLayout(frameCombinedLayout)

                    stateContentsGrid.addWidget(frameCombined, direction, frameNumber)

                    frameNumber = frameNumber + 1

            stateContentsGroupBox.setLayout(stateContentsGrid)
            stateContentsGroupBox.setFlat(True)

            scrollableStateContents = QtW.QScrollArea()
            scrollableStateContents.setWidget(stateContentsGroupBox)
            scrollableStateContents.setAlignment(QtC.Qt.AlignLeft)

            splitter.addWidget(scrollableStateContents)

        stateGroupBox = QtW.QGroupBox("States")
        stateLayout = FlowLayout()

        for stateName in self.currentRsi.states():
            state = self.currentRsi.states()[stateName]


            if len(state.icons[0]) == 0:
                image = PIL.Image.new('RGB', self.currentRsi.size)
            else:
                image = state.icons[0][0]

            stateIcon = Icon(stateName, image, iconSize)
            stateIcon.drillDown.connect(self.openState)
            
            stateNameLabel = EditableLabel(stateName)
            stateNameLabel.setMaximumWidth(stateIcon.iconWidth * stateNameFactor)
            stateNameLabel.edited.connect(self.renameState)

            stateCombinedLayout = QtW.QVBoxLayout()

            stateCombinedLayout.addWidget(stateIcon, alignment=QtC.Qt.AlignHCenter)
            stateCombinedLayout.addWidget(stateNameLabel, alignment=QtC.Qt.AlignHCenter)

            stateCombined = QtW.QWidget()
            stateCombined.setLayout(stateCombinedLayout)

            stateLayout.addWidget(stateCombined)


        stateGroupBox.setLayout(stateLayout)
        stateGroupBox.setFlat(True)

        scrollableState = QtW.QScrollArea()
        scrollableState.setWidget(stateGroupBox)
        scrollableState.setWidgetResizable(True)

        splitter.addWidget(scrollableState)

        configGroupBox = QtW.QGroupBox("Metadata")
        configLayout = QtW.QFormLayout()

        (x, y) = self.currentRsi.size()
        configLayout.addRow("Size:", QtW.QLabel(f'x: {x}, y: {y}'))
        
        license = self.currentRsi.license()
        licenseInput = QtW.QLineEdit()
        licenseInput.setText(license)
        licenseInput.textChanged.connect(self.currentRsi.updateLicense)
        configLayout.addRow("License:", licenseInput)

        copyright = self.currentRsi.copyright()
        copyrightInput = QtW.QLineEdit()
        copyrightInput.setText(copyright)
        copyrightInput.textChanged.connect(self.currentRsi.updateCopyright)
        configLayout.addRow("Copyright:", copyrightInput)

        configGroupBox.setLayout(configLayout)
        splitter.addWidget(configGroupBox)

        self.setCentralWidget(splitter)

    @QtC.Slot()
    def newRsi(self):
        if not self.closeCurrentRsi():
            return

        # TODO: get RSI size values in input
        self.currentRsi = CurrentRsi(Rsi((32, 32)), None)
        self.reloadRsi()

    @QtC.Slot()
    def openRsi(self):
        if not self.closeCurrentRsi():
            return

        rsiFile = QtW.QFileDialog.getExistingDirectory(self, 'Open RSI')

        if rsiFile == '':
            return

        self.currentRsi = CurrentRsi(Rsi.open(rsiFile), rsiFile)
        self.reloadRsi()

    @QtC.Slot()
    def saveRsi(self):
        if not self.currentRsi.hasPath():
            rsiPath = QtW.QFileDialog.getExistingDirectory(self, 'Save RSI')

            if rsiPath == '':
                return False

            self.currentRsi.setPath(rsiPath)

        self.currentRsi.save()
        return True

    def closeCurrentRsi(self):
        # TODO: Make this a proper "Do you want to save" dialog
        if self.currentRsi is not None:
            if not self.currentRsi.close():
                if self.saveRsi():
                    self.currentRsi.close()
                    self.currentRsi = None
                    self.currentState = None
                    return True
                else:
                    return False
            else:
                return True
        else:
            return True

    @QtC.Slot()
    def openState(self, stateName):
        self.currentState = CurrentState(self.currentRsi, stateName)
        self.reloadRsi()

    @QtC.Slot()
    def renameState(self, oldStateName, newStateName):
        if oldStateName == newStateName:
            return

        states = self.currentRsi.states()

        if newStateName in states:
            # TODO: confirm overwrite
            return

        self.currentRsi.renameState(oldStateName, newStateName)
        self.reloadRsi()

def editor():
    app = QtW.QApplication([])

    window = EditorWindow()
    window.showMaximized()

    exit(app.exec_())
