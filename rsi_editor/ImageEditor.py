# Helpers for opening an image in an editor

# Because RSI-editor is *not* an image editor, it delegates editing to a third
# party program

import PIL # type: ignore

import os
import subprocess
import tempfile

from typing import Optional

class ImageEditor():
    # Expects a PIL image
    def editImage(image : PIL.Image.Image) -> Optional[PIL.Image.Image]:
        temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tempPath = temp.name
    
        image.save(temp, format='PNG')
        temp.close()
    
        # TODO: not hardcode this
        result = subprocess.run(["gimp", tempPath])
    
        retValue = None
        if result.returncode == 0:
            retValue = PIL.Image.open(tempPath)

        os.unlink(tempPath)
        return retValue

