import rsi

# Wrapper class around the RSI API, for use in the editor
class Rsi():
    # Constructors
    def __init__(self, rsi):
        self.rsi = rsi

    def fromFile(rsiPath):
        return Rsi(rsi.Rsi.open(rsiPath))

    def new(x, y):
        return Rsi(rsi.Rsi((x, y)))

    # Convenience function

    def save(self, path):
        self.rsi.write(path)
        return True

    # Getters

    def states(self):
        return self.rsi.states

    def size(self):
        return self.rsi.size

    def license(self):
        return self.rsi.license or ''

    def copyright(self):
        return self.rsi.copyright or ''

    # Setters - return True if the RSI is changed

    def setLicense(self, licenseText):
        if self.rsi.license != licenseText:
            self.rsi.license = licenseText
            return True
        return False

    def setCopyright(self, copyrightText):
        if self.rsi.copyright != copyrightText:
            self.rsi.copyright = copyrightText
            return True
        return False

    def renameState(self, oldStateName, newStateName):
        if oldStateName != newStateName:
            state = self.rsi.get_state(oldStateName)
            self.rsi.states.pop(oldStateName)
            state.name = newStateName
            self.rsi.set_state(state, newStateName)
            return True
        return False

# Wrapper class around an RSI state, for use in the editor
class State():
    def __init__(self, parentRsi, stateName):
        self.state = parentRsi.states()[stateName]

    # Getters

    def name(self):
        return self.state.name

    def directions(self):
        return self.state.directions

    # Convenience function - get pairs of images and delays for the given direction
    def frames(self, direction):
        return zip(self.state.icons[direction], self.state.delays[direction])
