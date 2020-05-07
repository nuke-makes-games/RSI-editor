import PySide2.QtCore as QtC
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW

import PIL as PIL
import PIL.ImageQt as PILQt

from rsi import Rsi

rsiFileFilter = 'Robust Station Image (*.rsi);;RSI JSON metadata (*.json)'

class CurrentRsi():
    def __init__(self, rsi, path):
        self.rsi = rsi
        self.path = path
        self.dirty = False

    def close(self):
        if self.dirty:
            if not self.save():
                return False

        return True

    def save(self):
        if self.path is None or self.path == '':
            (self.path, _ ) = QtW.QFileDialog.getSaveFileName(self, 'Save RSI File', dir='', filter=rsiFileFilter)

            if self.rsiPath == '':
                return False

        self.rsi.write(self.path)
        self.dirty = False
        return True

    def states(self):
        return self.rsi.states

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

        stateGroupBox = QtW.QGroupBox("States")
        stateBox = QtW.QHBoxLayout()

        for stateName in self.currentRsi.states():
            state = self.currentRsi.states()[stateName]
            if len(state.icons[0]) == 0:
                image = PIL.Image.new('RGB', self.currentRsi.size)
            else:
                image = state.icons[0][0]

            stateLabel = QtW.QLabel()
            stateLabel.setPixmap(QtG.QPixmap.fromImage(PILQt.ImageQt(image)))

            stateBox.addWidget(stateLabel)


        stateGroupBox.setLayout(stateBox)
        splitter.addWidget(stateGroupBox)

        bottomLabel = QtW.QLabel()
        bottomLabel.setText("This is where the config goes.")
        splitter.addWidget(bottomLabel)

        self.setCentralWidget(splitter)

    @QtC.Slot()
    def newRsi(self):
        if self.currentRsi is not None:
            if not self.currentRsi.close():
                return

        # TODO: get RSI size values in input
        self.currentRsi = Rsi((32, 32))
        self.reloadRsi()

    @QtC.Slot()
    def openRsi(self):
        #(rsiFile, _) = QtW.QFileDialog.getOpenFileName(self, 'Open RSI File', dir='', filter=rsiFileFilter)
        rsiFile = QtW.QFileDialog.getExistingDirectory(self, 'Open RSI')

        if rsiFile == '':
            return

        self.currentRsi = CurrentRsi(Rsi.open(rsiFile), rsiFile)
        self.reloadRsi()

    @QtC.Slot()
    def saveRsi(self):
        if self.currentRsi is None:
            return

        self.currentRsi.save()

def editor():
    app = QtW.QApplication([])

    window = EditorWindow()
    window.showMaximized()

    exit(app.exec_())
