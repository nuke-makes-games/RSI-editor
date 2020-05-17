# Helpers for opening an image in an editor

# Because RSI-editor is *not* an image editor, it delegates editing to a third
# party program

import PIL # type: ignore

import os
import subprocess
import tempfile

from typing import List, Optional

class ImageEditor():
    # Expects a PIL image
    def editImage(image : PIL.Image.Image, command : List[str]) -> Optional[PIL.Image.Image]:
        temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tempPath = temp.name
    
        image.save(temp, format='PNG')
        temp.close()
    
        # `{}` is where the file path should be inserted
        result = subprocess.run([(tempPath if segment == '{}' else segment) for segment in command])
    
        retValue = None
        if result.returncode == 0:
            retValue = PIL.Image.open(tempPath)

        os.unlink(tempPath)
        return retValue

