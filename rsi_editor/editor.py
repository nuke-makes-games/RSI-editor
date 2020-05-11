import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

from .ImageEditor import ImageEditor
from .PixmapAnimation import PixmapAnimation
from .Rsi import Rsi, State, iconSize
from .AnimationView import AnimationView 

rsiFileFilter = 'Robust Station Image (*.rsi);;RSI JSON metadata (*.json)'

class EditorWindow(QtW.QMainWindow):
    def __init__(self):
        QtW.QMainWindow.__init__(self)
        self.setWindowTitle("RSI editor")

        self.undoStack = QtW.QUndoStack(self)

        self.editorMenu()

        # TODO: Reload session information
        self.currentRsi = None
        self.currentState = None

        self.contentLayout()

    def editorMenu(self):
        fileMenu = self.menuBar().addMenu("&File")

        # Set up new RSI
        newAction = fileMenu.addAction("&New")
        newAction.setShortcut(QtG.QKeySequence.New)
        newAction.triggered.connect(self.newRsi)

        # Set up file opening
        openAction = fileMenu.addAction("&Open")
        openAction.setShortcut(QtG.QKeySequence.Open)
        openAction.triggered.connect(self.openRsi)

        # Set up file saving
        saveAction = fileMenu.addAction("&Save")
        saveAction.setShortcut(QtG.QKeySequence.Save)
        saveAction.triggered.connect(self.saveRsi)

        saveAsAction = fileMenu.addAction("Save As")
        saveAsAction.setShortcut(QtG.QKeySequence.SaveAs)
        saveAsAction.triggered.connect(self.saveAsRsi)

        fileMenu.addSeparator()

        # TODO: Set up preferences
        preferencesAction = fileMenu.addAction("Preferences")
        preferencesAction.setShortcut(QtG.QKeySequence.Preferences)

        editMenu = self.menuBar().addMenu("&Edit")

        # Undo
        undoAction = editMenu.addAction("&Undo")
        undoAction.setShortcut(QtG.QKeySequence.Undo)
        undoAction.triggered.connect(self.undoStack.undo)

        # Redo
        redoAction = editMenu.addAction("&Redo")
        redoAction.setShortcut(QtG.QKeySequence.Redo)
        redoAction.triggered.connect(self.undoStack.redo)

    def contentLayout(self):
        splitter = QtW.QSplitter()
        splitter.setOrientation(QtC.Qt.Vertical)

        self.stateContents = AnimationView()
        self.stateContents.setIconSize(iconSize)
        self.stateContents.clicked.connect(self.stateContentsDrillDown)

        self.stateList = QtW.QListView()
        self.stateList.setViewMode(QtW.QListView.IconMode)
        self.stateList.setIconSize(iconSize)
        self.stateList.setMovement(QtW.QListView.Snap)
        self.stateList.setSelectionRectVisible(True)
        self.stateList.setUniformItemSizes(True)
        self.stateList.setWordWrap(True)
        self.stateList.setSelectionMode(QtW.QAbstractItemView.ExtendedSelection)
        self.stateList.clicked.connect(self.stateListDrillDown)

        stateLayout = QtW.QHBoxLayout()
        stateLayout.addWidget(self.stateList)
        stateWidget = QtW.QWidget()
        stateWidget.setLayout(stateLayout)

        self.configGroupBox = QtW.QGroupBox("Metadata")
        self.configGroupBox.setLayout(QtW.QFormLayout(self.configGroupBox))

        splitter.addWidget(self.stateContents)
        splitter.addWidget(stateWidget)
        splitter.addWidget(self.configGroupBox)

        self.setCentralWidget(splitter)

    def clearLayout(self, layout):
        while layout.count() > 0:
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().setParent(None)

    def reloadRsi(self):
        # Clear the grid
        self.stateContents.reset()

        if self.currentState is not None:
            self.stateContents.setModel(self.currentState.model)

        self.stateList.reset()
        self.clearLayout(self.configGroupBox.layout())

        if self.currentRsi is not None:
            self.stateList.setModel(self.currentRsi.stateList)

            (x, y) = self.currentRsi.size()
            self.configGroupBox.layout().addRow("Size:", QtW.QLabel(f'x: {x}, y: {y}'))

            license = self.currentRsi.license()
            licenseInput = QtW.QLineEdit()
            licenseInput.setText(license)
            licenseInput.textChanged.connect(self.currentRsi.setLicense)
            self.configGroupBox.layout().addRow("License:", licenseInput)

            copyright = self.currentRsi.copyright()
            copyrightInput = QtW.QLineEdit()
            copyrightInput.setText(copyright)
            copyrightInput.textChanged.connect(self.currentRsi.setCopyright)
            self.configGroupBox.layout().addRow("Copyright:", copyrightInput)

    @QtC.Slot()
    def newRsi(self):
        if not self.closeCurrentRsi():
            return

        # TODO: get RSI size values in input
        self.currentRsi = Rsi.new(32, 32)
        self.reloadRsi()

    @QtC.Slot()
    def openRsi(self):
        if not self.closeCurrentRsi():
            return

        rsiFile = QtW.QFileDialog.getExistingDirectory(self, 'Open RSI')

        if rsiFile == '':
            return

        self.currentRsi = Rsi.fromFile(rsiFile)
        self.setWindowFilePath(rsiFile)

        self.reloadRsi()

    @QtC.Slot()
    def saveRsi(self):
        if self.currentRsi is None:
            return False

        if self.windowFilePath() is None and not self.setRsiPath():
            return False

        self.currentRsi.save(self.windowFilePath())
        return True

    @QtC.Slot()
    def saveAsRsi(self):
        if self.currentRsi is None:
            return False

        if not self.setRsiPath():
            return False

        return self.saveRsi()

    def setRsiPath(self):
        rsiPath = QtW.QFileDialog.getExistingDirectory(self, 'Save RSI')

        if rsiPath == '':
            return False

        self.setWindowFilePath(rsiPath)
        return True

    def closeCurrentRsi(self):
        if self.currentRsi is not None and self.isWindowModified():
            confirmCloseReply = QtW.question(
                    self,
                    'Close without saving?',
                    'The RSI has unsaved changes - close it anyways?',
                    buttons=QtW.QMessageBox.Save|QtW.QMessageBox.Discard|QtW.QMessageBox.Cancel,
                    defaultButton=QtW.QMessageBox.Save)

            if confirmCloseReply == QtW.QMessageBox.Save:
                response = self.saveRsi()
            if confirmCloseReply == QtW.QMessageBox.Discard:
                response = True
            if confirmCloseReply == QtW.QMessageBox.Cancel:
                response = False
        else:
            response = True

        if response:
            self.currentRsi = None
            self.currentState = None

        return response

    @QtC.Slot()
    def stateListDrillDown(self, stateListIndex):
        state = self.stateList.model().getState(stateListIndex)
        self.currentState = State(self.currentRsi, state.name)
        self.reloadRsi()

    @QtC.Slot()
    def stateContentsDrillDown(self, stateIndex):
        image = self.stateContents.model().frame(stateIndex)
        edited = ImageEditor.editImage(image)

        if edited is not None:
            self.stateContents.model().setFrame(stateIndex, edited)


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
