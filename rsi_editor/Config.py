from __future__ import annotations

from os import makedirs, path
import toml
import PySide2.QtCore as QtC
import PySide2.QtWidgets as QtW

from typing import MutableMapping, List, Optional

class Config():
    editorCommand : Optional[List[str]]

    def __init__(self, dictionary : MutableMapping[str, str]):

        if 'editor' in dictionary:
            commandString = dictionary['editor']
            self.editorCommand = commandString.split()
        else:
            self.editorCommand = None

    def dict(self) -> MutableMapping[str, str]:
        contents = {}

        if self.editorCommand is not None:
            contents['editor'] = ' '.join(self.editorCommand)

        return contents

    @classmethod
    def load(cls) -> Config:
        configPath = QtC.QStandardPaths.locate(
                QtC.QStandardPaths.AppConfigLocation,
                'config.toml',
                options = QtC.QStandardPaths.LocateFile)

        if configPath != '':
            configDict = toml.load(configPath)
            return cls(configDict)
        else:
            return cls({})

    def save(self) -> None:
        configFolder = QtC.QStandardPaths.writableLocation(QtC.QStandardPaths.AppConfigLocation)

        if configFolder == '':
            raise PermissionError("Could not write config to config folder!")

        makedirs(configFolder, exist_ok=True)

        with open(path.join(configFolder, 'config.toml'), 'w') as configFile:
            toml.dump(self.dict(), configFile)

    def hasEditor(self) -> bool:
        return self.editorCommand is not None

class ConfigEditor(QtW.QDialog):
    def __init__(self, config : Config, parent : Optional[QtC.QObject] = None):
        QtW.QDialog.__init__(self, parent)

        self.setWindowTitle('Preferences')
        self.setSizeGripEnabled(True)

        self.config = config

        overallLayout = QtW.QVBoxLayout()

        configForm  = QtW.QFormLayout()
        
        self.editorCommandEdit = QtW.QLineEdit()
        if config.editorCommand is not None:
            self.editorCommandEdit.setText(' '.join(config.editorCommand))

        configForm.addRow('Image editor command:', self.editorCommandEdit)
        
        configWidget = QtW.QGroupBox('Preferences')
        configWidget.setLayout(configForm)
        configWidget.sizePolicy().setVerticalPolicy(QtW.QSizePolicy.MinimumExpanding)

        buttonLayout = QtW.QHBoxLayout()

        cancelButton = QtW.QPushButton('Cancel')
        cancelButton.clicked.connect(lambda _checked: self.reject())
        cancelButton.setDefault(False)
        
        saveButton = QtW.QPushButton('Save')
        saveButton.clicked.connect(lambda _checked: self.accept())
        saveButton.setDefault(True)

        buttonLayout.addWidget(cancelButton)
        buttonLayout.addWidget(saveButton)

        buttonsWidget = QtW.QWidget()
        buttonsWidget.setLayout(buttonLayout)
        buttonsWidget.setSizePolicy(QtW.QSizePolicy(QtW.QSizePolicy.Preferred, QtW.QSizePolicy.Fixed))

        overallLayout.addWidget(configWidget)
        overallLayout.addWidget(buttonsWidget)

        self.setLayout(overallLayout)

    # Returns if the config was edited
    def edit(self) -> bool:
        result = self.exec()

        if result == QtW.QDialog.Accepted:
            self.config.editorCommand = self.editorCommandEdit.text().split()
            return True
        else:
            return False
