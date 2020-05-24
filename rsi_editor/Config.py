from __future__ import annotations

from os import makedirs, path
import toml
import PySide2.QtCore as QtC
import PySide2.QtWidgets as QtW

from typing import Any, MutableMapping, List, Optional

class Config():
    editorCommand : Optional[List[str]]

    def __init__(self, dictionary : MutableMapping[str, Any]):

        if 'editor' in dictionary:
            commandString = dictionary['editor']

            self.editorCommand = commandString.split()
        else:
            self.editorCommand = None

        if 'formatMetadata' in dictionary:
            self.formatMetadata = dictionary['formatMetadata']
        else:
            self.formatMetadata = True

        if 'metadataIndent' in dictionary:
            self.metadataIndent = dictionary['metadataIndent']
        else:
            self.metadataIndent = 4

    def dict(self) -> MutableMapping[str, Any]:
        contents = {}

        if self.editorCommand is not None:
            contents['editor'] = ' '.join(self.editorCommand)

        contents['formatMetadata'] = self.formatMetadata
        contents['metadataIndent'] = self.metadataIndent

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

        self.formatMetadataEdit = QtW.QCheckBox()
        if config.formatMetadata is not None:
            self.formatMetadataEdit.setChecked(config.formatMetadata)

        configForm.addRow('Format metadata JSON:', self.formatMetadataEdit)

        self.metadataIndentEdit = QtW.QSpinBox()
        self.metadataIndentEdit.setValue(config.metadataIndent)
        
        configForm.addRow('JSON indentation level:', self.metadataIndentEdit)

        buttonBox = QtW.QDialogButtonBox(QtW.QDialogButtonBox.Cancel
                             | QtW.QDialogButtonBox.Save)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        overallLayout.addWidget(configWidget)
        overallLayout.addWidget(buttonBox)

        self.setLayout(overallLayout)

    # Returns if the config was edited
    def edit(self) -> bool:
        result = self.exec()

        if result == QtW.QDialog.Accepted:
            self.config.editorCommand = self.editorCommandEdit.text().split()
            self.config.formatMetadata = self.formatMetadataEdit.isChecked()
            self.config.metadataIndent = self.metadataIndentEdit.value()
            return True
        else:
            return False
