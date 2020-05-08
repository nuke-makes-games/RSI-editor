import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

from rsi import Rsi

from .FlowLayout import FlowLayout
from .LabelledIcon import LabelledIcon
from .PixmapAnimation import PixmapAnimation

rsiFileFilter = 'Robust Station Image (*.rsi);;RSI JSON metadata (*.json)'

# TODO: Have this be configured by zooming in and out
iconSize = QtC.QSize(50, 50)

class CurrentRsi():
    def __init__(self, rsi, path):
        self.rsi = rsi
        self.path = path
        self.dirty = False
        self.currentState = None

    def close(self, force=False):
        if self.dirty and not force:
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

    @QtC.Slot()
    def renameState(self, oldStateName, newStateName):
        state = self.rsi.get_state(oldStateName)
        self.rsi.states.pop(oldStateName)
        state.name = newStateName
        self.rsi.set_state(state, newStateName)
        self.dirty = True

    def openState(self, stateName):
        self.currentState = CurrentState(self, stateName)

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

        if self.currentRsi.currentState is not None:
            stateContentsGroupBox = QtW.QGroupBox(self.currentRsi.currentState.name())
            stateContentsGrid = QtW.QGridLayout()

            for direction in range(self.currentRsi.currentState.directions()):
                directionAnimLabel = QtW.QLabel()
                directionAnim = QtC.QSequentialAnimationGroup(directionAnimLabel)
                frameNumber = 0

                for (image, delay) in self.currentRsi.currentState.frames(direction):
                    frameID = f'{self.currentRsi.currentState.name()}_{direction}_{frameNumber}'
                    frameIcon = LabelledIcon(frameID, str(delay), image, iconSize)

                    directionAnim.addAnimation(PixmapAnimation(directionAnimLabel, frameIcon.icon.pixmap(), delay * 1000))

                    #TODO: Editing the frame!
                    #TODO: Changing the delay
                    stateContentsGrid.addWidget(frameIcon, direction, frameNumber)

                    frameNumber = frameNumber + 1

                stateContentsGrid.addWidget(directionAnimLabel, direction, frameNumber)
                directionAnim.setLoopCount(-1)
                directionAnim.start()

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

            stateIcon = LabelledIcon(stateName, stateName, image, iconSize)
            
            stateIcon.drillDown.connect(self.openState)
            stateIcon.labelEdited.connect(self.renameState)
            
            stateLayout.addWidget(stateIcon)


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
        if self.currentRsi is None:
            return

        if not self.currentRsi.hasPath():
            rsiPath = QtW.QFileDialog.getExistingDirectory(self, 'Save RSI')

            if rsiPath == '':
                return False

            self.currentRsi.setPath(rsiPath)

        self.currentRsi.save()
        return True

    def closeCurrentRsi(self):
        if self.currentRsi is not None:
            if not self.currentRsi.close():
                confirmCloseDialog = QtW.QMessageBox(
                        QtW.QMessageBox.NoIcon,
                        'Close without saving?', 
                        'The RSI has unsaved changes - close it anyways?',
                        parent=self,
                        buttons=QtW.QMessageBox.Save|QtW.QMessageBox.Discard|QtW.QMessageBox.Cancel)

                confirmCloseDialog.buttonClicked.connect(lambda button: self.closeCurrentRsiByDialog(confirmCloseDialog.buttonRole(button)))
                confirmCloseDialog.exec()

                return False
            else:
                return True
        else:
            return True

    @QtC.Slot()
    def closeCurrentRsiByDialog(self, buttonRole):
        # Accept = save the file
        if buttonRole == QtW.QMessageBox.AcceptRole:
            if self.saveRsi():
                self.currentRsi.closeRsi()
        # Destructive = close without saving
        if buttonRole == QtW.QMessageBox.DestructiveRole:
            self.currentRsi.close(force=True)
        # Reject = cancel closing
        if buttonRole == QtW.MessageBox.RejectRole:
            return

    @QtC.Slot()
    def openState(self, stateName):
        self.currentRsi.openState(stateName)
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
