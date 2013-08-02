import os

class File():
    def __init__(self, baseFolder, file):
        self.baseFolder    = baseFolder
        self.currentFolder = baseFolder
        self.file          = file

    def exists(self, folder, file):
        path = os.path.join(folder,file)
        return os.path.exists(path)

    def upward(self):
        while (not self.exists(self.currentFolder, self.file)) :
            self.currentFolder = os.path.dirname(self.currentFolder)
            if '/' == self.currentFolder :
                raise Exception ("Could not find '%s'. I started at %s and went all the way up to the root folder" % (self.file, self.baseFolder))

            return self.upward()

        return self.currentFolder
