import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

from .ImageEditor import ImageEditor
from .Rsi import Rsi, State, iconSize
from .AnimationView import AnimationView 

rsiFileFilter = 'Robust Station Image (*.rsi);;RSI JSON metadata (*.json)'
dmiFileFilter = 'DreamMaker Image (*.dmi)'

class EditorWindow(QtW.QMainWindow):
    def __init__(self):
        QtW.QMainWindow.__init__(self)
        self.setWindowTitle("RSI editor[*]")

        self.undoStack = QtW.QUndoStack(self)

        self.editorMenu()

        # TODO: Reload session information
        self.currentRsi = None
        self.currentState = None

        self.contentLayout()

        self.contentMenus()

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

        importAction = fileMenu.addAction("&Import")
        importAction.triggered.connect(self.importDmi)

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

        # Undo history
        undoMenu = editMenu.addMenu("Undo history")

        undoHistory = QtW.QUndoView(parent=undoMenu)
        undoHistory.setStack(self.undoStack)

        undoMenu.addAction(QtW.QWidgetAction(undoHistory))

    def contentMenus(self):
        self.stateContentsMenu()

    def stateContentsMenu(self):
        editorAction = self.stateContents.addCellAction("Open in editor...")
        editorAction.indexTriggered.connect(self.stateContentsEdit)

        # TODO: important actions
        #insertAction = self.stateContents.addCellAction("Insert image")
        #insertAction.indexTriggered.connect(self.stateContentsInsert)

        #insertFrameAction = self.stateContents.addCellAction("Insert frame")
        #insertFrameAction.indexTriggered.connect(self.stateContentsInsertFrame)

        #deleteAction = self.stateContents.addCellAction("Delete image")
        #deleteAction.indexTriggered.connect(self.stateContentsDelete)

        #deleteFrameAction = self.stateContents.addCellAction("Delete frame")
        #deleteFrameAction.indexTriggered.connect(self.stateContentsDeleteFrame)

    def contentLayout(self):
        splitter = QtW.QSplitter()
        splitter.setOrientation(QtC.Qt.Vertical)

        self.stateContents = AnimationView()
        self.stateContents.setIconSize(iconSize)

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
        
        self.sizeInfo = QtW.QLabel()

        self.licenseInput = QtW.QLineEdit()
        self.licenseInput.setEnabled(False)
        self.licenseInput.editingFinished.connect(self.updateLicense)

        self.copyrightInput = QtW.QLineEdit()
        self.copyrightInput.setEnabled(False)
        self.copyrightInput.editingFinished.connect(self.updateCopyright)
        
        configLayout = QtW.QFormLayout()
        configLayout.addRow("Size:", self.sizeInfo)
        configLayout.addRow("License:", self.licenseInput)
        configLayout.addRow("Copyright:", self.copyrightInput) 

        self.configGroupBox = QtW.QGroupBox("Metadata")
        self.configGroupBox.setLayout(configLayout)

        splitter.addWidget(self.stateContents)
        splitter.addWidget(stateWidget)
        splitter.addWidget(self.configGroupBox)


        self.setCentralWidget(splitter)

    def reloadRsi(self):
        # Clear the grid
        self.stateContents.reset()
        self.stateList.reset()

        if self.currentRsi is not None:
            self.stateList.setModel(self.currentRsi)

            self.currentRsi.stateRenamed.connect(self.renameState)

            (x, y) = self.currentRsi.size
            self.sizeInfo.setText(f'x: {x}, y: {y}')

            license = self.currentRsi.license
            self.licenseInput.setText(license)
            self.licenseInput.setEnabled(True)
            self.currentRsi.licenseChanged.connect(lambda : self.licenseInput.setText(self.currentRsi.license))

            copyright = self.currentRsi.copyright
            self.copyrightInput.setText(copyright)
            self.copyrightInput.setEnabled(True)
            self.currentRsi.copyrightChanged.connect(lambda : self.copyrightInput.setText(self.currentRsi.copyright))
        else:
            self.sizeInfo.setText('')
            self.licenseInput.setText('')
            self.licenseInput.setEnabled(False)
            self.copyrightInput.setText('')
            self.copyrightInput.setEnabled(False)
    

    @QtC.Slot()
    def newRsi(self):
        if not self.closeCurrentRsi():
            return

        # TODO: get RSI size values in input
        self.currentRsi = Rsi.new(32, 32)
        self.setWindowFilePath('')
        self.setWindowModified(False)
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
        self.setWindowModified(False)

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

    @QtC.Slot()
    def importDmi(self):
        if not self.closeCurrentRsi():
            return

        (dmiFile, _) = QtW.QFileDialog.getOpenFileName(self, 'Import DMI', filter=dmiFileFilter)

        if dmiFile == '':
            return

        self.currentRsi = Rsi.fromDmi(dmiFile)
        self.setWindowFilePath('')
        self.setWindowModified(True)

        self.reloadRsi()

    def setRsiPath(self):
        rsiPath = QtW.QFileDialog.getExistingDirectory(self, 'Save RSI')

        if rsiPath == '':
            return False

        self.setWindowFilePath(rsiPath)
        return True

    def closeCurrentRsi(self):
        if self.currentRsi is not None and self.isWindowModified():
            confirmCloseReply = QtW.QMessageBox.question(
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
        self.stateContents.setModel(self.currentState.model)

    @QtC.Slot()
    def stateContentsEdit(self, stateIndex):
        image = self.stateContents.model().frame(stateIndex)
        edited = ImageEditor.editImage(image)

        if edited is not None:
            self.stateContents.model().setFrame(stateIndex, edited)


    @QtC.Slot()
    def renameState(self, oldStateName, newStateName):
        if oldStateName != newStateName:
            self.undoStack.push(RenameStateCommand(self, oldStateName, newStateName))
            self.setWindowModified(True)

    @QtC.Slot()
    def updateLicense(self):
        if self.licenseInput.text() != self.currentRsi.license:
            self.undoStack.push(SetLicenseCommand(self, self.currentRsi.license, self.licenseInput.text()))
            self.setWindowModified(True)

    @QtC.Slot()
    def updateCopyright(self):
        if self.copyrightInput.text() != self.currentRsi.copyright:
            self.undoStack.push(SetCopyrightCommand(self, self.currentRsi.copyright, self.copyrightInput.text()))
            self.setWindowModified(True)

##############################
### COMMANDS FOR UNDO/REDO ###
#############################

SetLicenseCommandId = 100
SetCopyrightCommandId = 101

class SetLicenseCommand(QtW.QUndoCommand):
    def __init__(self, editor, oldLicense, newLicense):
        QtW.QUndoCommand.__init__(self)
        self.editor = editor
        self.oldLicense = oldLicense
        self.newLicense = newLicense

    def id(self):
        return SetLicenseCommandId

    def text(self):
        return 'Edit license'

    def mergeWith(self, other):
        if other.id() != self.id():
            return False

        self.newLicense = other.newLicense
        return True

    def redo(self):
        self.editor.currentRsi.setLicense(self.newLicense)

    def undo(self):
        self.editor.currentRsi.setLicense(self.oldLicense)

class SetCopyrightCommand(QtW.QUndoCommand):
    def __init__(self, editor, oldCopyright, newCopyright):
        QtW.QUndoCommand.__init__(self)
        self.editor = editor
        self.oldCopyright = oldCopyright
        self.newCopyright = newCopyright

    def id(self):
        return SetCopyrightCommandId

    def text(self):
        return 'Edit copyright'

    def mergeWith(self, other):
        if other.id() != self.id():
            return False

        self.newCopyright = other.newCopyright
        return True

    def redo(self):
        self.editor.currentRsi.setCopyright(self.newCopyright)

    def undo(self):
        self.editor.currentRsi.setCopyright(self.oldCopyright)

class NewStateCommand(QtW.QUndoCommand):
    def __init__(self, editor):
        QtW.QUndoCommand.__init__(self)

        self.editor = editor

        states = self.editor.currentRsi.states

        newStateNumber = 1
        while f'NewState{newStateNumber}' in states:
            newStateNumber = newStateNumber + 1

        self.newStateName = f'NewState{newStateNumber}'

    def id(self):
        return -1

    def text(self):
        return 'Create new state'

    def redo(self): 
        self.editor.currentRsi.addState(self.newStateName)

    def undo(self):
        self.editor.currentRsi.removeState(self.newStateName)

class RenameStateCommand(QtW.QUndoCommand):
    def __init__(self, editor, oldStateName, newStateName):
        QtW.QUndoCommand.__init__(self)

        self.editor = editor
        self.oldStateName = oldStateName
        self.newStateName = newStateName
        self.overwritten = None

    def id(self):
        return -1

    def text(self):
        return 'Rename state'

    def redo(self):
        self.overwritten = self.editor.currentRsi.removeState(self.newStateName)
        self.editor.currentRsi.renameState(self.oldStateName, self.newStateName)

    def undo(self):
        self.editor.currentRsi.renameState(self.newStateName, self.oldStateName)
        if self.overwritten != None:
            self.editor.currentRsi.addState(self.newStateName, self.overwritten)

def editor():
    app = QtW.QApplication([])

    window = EditorWindow()
    window.showMaximized()

    exit(app.exec_())
