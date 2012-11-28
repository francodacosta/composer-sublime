"""
    Composer Integration for Sublime Text 2

    @author  Nuno Franco da Costa <nuno@francodacosta.com>
    @license BSD - see LICENSE.md
    @link    git@github.com:francodacosta/composer-sublime.git
"""

import sublime
import sublime_plugin
import functools
import os
import subprocess
import time
import thread
import json


def debug_msg(msg):
    """
        Debug messages
    """
    if Prefs.debug == 1:
        print "[Composer] " + msg

class Prefs:
    """
        Plugin preferences
    """

    @staticmethod
    def load():
        settings = sublime.load_settings('composer-sublime.sublime-settings')

        Prefs.debug                   = settings.get('show_debug', 1)
        Prefs.showOutput              = settings.get('show_output')
        Prefs.showStatus              = settings.get('show_status')

        Prefs.composerCommand         = settings.get('composer_command')
        Prefs.composerFile            = settings.get('composer_file', 'composer.json')

        Prefs.composerInstallExtra    = settings.get('composer_install_extra')
        Prefs.composerUpdateExtra     = settings.get('composer_update_extra')
        Prefs.composerSelfUpdateExtra = settings.get('composer_selfupdate_extra')

Prefs.load()


class FolderLocator():
    def __init__(self, baseFolder):
        self.baseFolder    = baseFolder
        self.currentFolder = baseFolder

    def exists(self, folder, file):
        path = os.path.join(folder,file)
        return os.path.exists(path)

    def locate(self, file):
        while (not self.exists(self.currentFolder, file)) :
            debug_msg("looking for %s in %s" % (file, self.currentFolder))
            self.currentFolder = os.path.dirname(self.currentFolder)
            if '/' == self.currentFolder :
                raise Exception ("Could not find '%s'. I started at %s and went all the way up to the root folder" % (file,self.baseFolder))
            return self.locate(file)

        debug_msg("found file in %s" % (self.currentFolder))
        return self.currentFolder

class OutputWindow(object):
    def __init__(self, window, name = 'composer'):
        self.window       = window
        self.name         = name
        self.outputWindow = None
        self.enabled      = 1

    def setEnabled(self, bool):
        self.enabled = bool


    def getOutputWindow(self):
        if (None is self.outputWindow):
            self.outputWindow = self.window.get_output_panel(self.name)
            self.clear()

        return self.outputWindow

    def show(self):
        if self.enabled is False:
            return

        self.getOutputWindow()
        self.window.run_command("show_panel", {"panel": "output." + self.name})

    def clear(self):
        outputWindow = self.getOutputWindow()
        outputWindow.set_read_only(False)
        edit = outputWindow.begin_edit()
        outputWindow.erase(edit, sublime.Region(0, outputWindow.size()))
        outputWindow.end_edit(edit)
        outputWindow.set_read_only(True)


    def write(self, data):
        if self.enabled is False :
            return

        str = data.decode("utf-8")
        str = str.replace('\r\n', '\n').replace('\r', '\n')
        outputWindow = self.getOutputWindow()
        self.show()

        # selection_was_at_end = (len(self.output_view.sel()) == 1
        #  and self.output_view.sel()[0]
        #    == sublime.Region(self.output_view.size()))
        self.outputWindow.set_read_only(False)
        edit = outputWindow.begin_edit()
        outputWindow.insert(edit, outputWindow.size(), str)
        #if selection_was_at_end:
        outputWindow.show(outputWindow.size())
        outputWindow.end_edit(edit)
        outputWindow.set_read_only(True)

class Worker(object):

    def __init__(self, command, workingDir, outputWindow = None, statusBar = None):
        self.command      = command
        self.workingDir   = workingDir
        self.outputWindow = outputWindow
        self.statusBar    = statusBar
        self.proc         = None
        self.counter = 0

    def doWork(self):
        self.startStatusProgress()
        shell = os.name == 'nt'

        self.appendData("executing: %s\n" % ' '.join(self.command))

        try:
            self.proc = subprocess.Popen(
                self.command,
                shell  = shell,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                cwd    = self.workingDir
            )

            if self.proc.stdout:
                thread.start_new_thread(self.readStdOut, ())
            if self.proc.stderr:
                thread.start_new_thread(self.readStdErr, ())

        except Exception, e:
            msg = "Error: %s" % e
            debug_msg(msg)
            self.appendData(msg)
            self.statusBar.stop = True
            self.statusBar.error = True
            # self.stopStatusProgress()
            thread.start_new_thread(self.statusBar.timedMessage,(msg))

    def appendData(self, data):
        if self.outputWindow is None:
            debug.debug_msg("Skipping output window messages")
            return
        self.counter = self.counter + 1
        self.outputWindow.window.active_view().set_status("Composer", "%s" % self.counter)
        self.outputWindow.write(data)

    def startStatusProgress(self):
        if self.statusBar is None:
            debug.debug_msg("Skipping status bar messages")
            return
        self.statusBar.start()

    def stopStatusProgress(self):
        if self.statusBar is None:
            debug.debug_msg("Skipping status bar messages")
            return
        self.statusBar.stop = True
        # self.statusBar.clear()

    def readStdOut(self):
        while True:
            data = os.read(self.proc.stdout.fileno(), 2 ** 15)
            if "" == data :
                self.proc.stdout.close()
                self.appendData("\n-- Terminated -- \n")
                self.statusBar.stop = True
                break
            else:
                sublime.set_timeout(functools.partial(self.appendData, data), 0)

    def readStdErr(self):
        while True:
            data = os.read(self.proc.stderr.fileno(), 2 ** 15)
            if "" == data :
                self.proc.stderr.close()
                # self.appendData("\n--- Execution Finished ---")
                #
                break
            else:
                sublime.set_timeout(functools.partial(self.appendData, data), 0)
        pass

class StatusMessage():
    def __init__(self, view):
        self.view = view
        self.stop = False
        self.enabled = False
        self.error = False

    def setEnabled(self, boolean):
        self.enabled = boolean

    def message(self, msg):
        if self.enabled is False :
            return

        self.view.set_status("composer", msg )

    def timedMessage(self, msg, sleep = 5):
         self.message(msg)
         time.sleep(sleep)
         self.clear()

    def clear(self):
        self.view.erase_status('composer')

    def showStatusProgress(self, progress = 1, size=10):
        # t=0
        while self.stop is False:
            if progress ==  2 * size:
                progress = 0

            if progress < size :
                before = progress + 1
                after = (size ) - before
            else:
                before = size - progress % size -1
                after = (size ) - before

            msg = "Running Composer [%s=%s]" % (' ' * before, ' ' * after)

            self.message(msg)
            #sublime.set_timeout(functools.partial(self.view.set_status, msg), 0)
            time.sleep(0.1)
            progress += 1
            # t +=1
            # print t
            # if t == 20:
            #     break
        if self.error is False :
            self.message("Composer finished")
            time.sleep(3)
        self.clear()

    def start(self):
        thread.start_new_thread(self.showStatusProgress, ())



class BaseComposerCommand(sublime_plugin.TextCommand):

    def showTimedStatusMessage(self, msg):
        sm = self.getStatusMessage()
        sm.timedMessage(msg)

    def locateComposerJsonFolder(self):
        locator = FolderLocator(os.path.dirname(self.view.file_name()))
        return locator.locate(Prefs.composerFile)

    def getOutputWindow(self):
        outputWindow = OutputWindow(self.view.window())
        outputWindow.setEnabled(Prefs.showOutput)
        outputWindow.clear()

        return outputWindow

    def prepareCommandList(self, binary, command, args):
        command = [binary, command]
        if (len(args) > 0) :
            command = command + args

        return  command

    def getStatusMessage(self):
        sm = StatusMessage(self.view)
        sm.setEnabled(Prefs.showStatus)

        return sm

    def statusMessage(self, msg, statusMessage):
        statusMessage.message(msg)
        time.sleep(5)
        statusMessage.clear()

    def go(self, binary, command, args):
        self.binary = binary
        self.command = command
        self.args =args

        outputWindow = self.getOutputWindow()
        outputWindow.write("-- Starting Composer --\n")
        outputWindow.write("binary   : %s\n"   % (self.binary,))
        outputWindow.write("command  : %s\n"   % (self.command,))
        outputWindow.write("arguments: %s\n\n" % (' '.join(self.args),))

        statusMessage = self.getStatusMessage()


        cmd = self.prepareCommandList(
            binary  = self.binary,
            command = self.command,
            args    = self.args
        )

        try:
            workingDir = self.locateComposerJsonFolder()
            os.chdir(workingDir)
        except Exception, e :
            outputWindow.write("Error: : %s" % e)
            msg = "[ERROR] Composer.json not found"
            thread.start_new_thread(self.statusMessage, (msg, statusMessage))
            # statusMessage.message('Could not find composer.json')
            # time.sleep(3)
            # statusMessage.clear()
            #sublime.set_timeout(functools.partial(self.statusMessage, (msg, statusMessage)), 3)


            return

        worker = Worker(
            command      = cmd,
            workingDir   = workingDir,
            outputWindow = outputWindow,
            statusBar    = statusMessage
        )

        worker.doWork()

class Packagist(object):
    def getPackages(self):
        pass

    def searchPackages(self):
        pass

class ComposerJsonPackages(object):
    def __init__(self):
        self.packages = []

    def addPackage(self, name, version = '*'):
        self.packages.append([name, version])

    def removePackage(self, index):
        del (self.packages[index])

    def toList(self):
        return self.packages

    def toDict(self):
        ret = {}
        for key, data in self.packages:
            ret[key] = data

        return ret

class ComposerJsonFileLoader(object):
    def __init__(self, file):
        self.composerFile = file
        self.packageList = None

        self.getPackages()

    def getPackages(self):

        if self.packageList is None:
            require = self.toJson()['require']
            packageList = ComposerJsonPackages()

            for key in require:
                packageList.addPackage(key, require[key])

            self.packageList = packageList

        return self.packageList

    def removePackage(self, index):
        self.packageList.removePackage(index)

    def addPackage(self, name, version = '*'):
        print "before: ", len (self.packageList.toList())
        self.packageList.addPackage(name, version)
        print "after: ", len (self.packageList.toList())


    def toJson(self):
        return json.load(open(self.composerFile))
        pass

    def save(self):
        jsonObj = self.toJson()
        jsonObj['require'] = self.packageList.toDict()

        json.dump(jsonObj, open(self.composerFile, 'w'),indent=4 )

class ComposerInstallCommand(BaseComposerCommand):
    def run(self, edit):
        bin  = Prefs.composerCommand
        cmd  = 'install'
        args = Prefs.composerInstallExtra

        self.go(bin, cmd, args)

class ComposerUpdateCommand(BaseComposerCommand):
    def run(self, edit):
        bin  = Prefs.composerCommand
        cmd  = 'update'
        args = Prefs.composerUpdateExtra

        self.go(bin, cmd, args)

class ComposerSelfUpdateCommand(BaseComposerCommand):
    def run(self, edit):
        bin  = Prefs.composerCommand
        cmd  = 'self-update'
        args = Prefs.composerSelfUpdateExtra

        self.go(bin, cmd, args)

class EditComposerFileCommand(BaseComposerCommand):
    def run(self, edit):
        composerJsonFile = os.path.join(self.locateComposerJsonFolder(), 'composer.json')
        self.view.window().open_file(composerJsonFile)

class ComposerRemovePackageCommand(BaseComposerCommand):
    def run(self, edit):
        self.composerJson = ComposerJsonFileLoader(os.path.join(self.locateComposerJsonFolder(), 'composer.json') )

        packages = self.composerJson.getPackages().toList()
        self.view.window().show_quick_panel(packages, self.removePackage)

    def removePackage(self, index):
        try:
            self.composerJson.removePackage(index)
            self.composerJson.save()
            thread.start_new_thread(self.showTimedStatusMessage, ("package removed",))
        except Exception, e:
            ow = OutputWindow(self.view.window())
            ow.write("Composer Error:\n\t" )
            ow.write("%s" % e)

class ComposerAddPackageCommand(BaseComposerCommand):
    def run(self, edit):
         self.input = self.view.window().show_input_panel("Package to add:", "Syntax: package name : version (if not provided defaults to *)", self.doAddPackage, None, None)
         self.input.sel().add(sublime.Region(0, 100))

    def doAddPackage(self, rawPackage):
        try:
            self.composerJson = ComposerJsonFileLoader(os.path.join(self.locateComposerJsonFolder(), 'composer.json') )

            splitInput = rawPackage.split(':')
            name = splitInput[0]
            if 1 == len(splitInput) :
                version = "*"
            else:
                version =splitInput[1]

            if 0 == len(name):
                raise Exception('Please provide a package name')

            self.composerJson.addPackage(name, version)
            self.composerJson.save()
            thread.start_new_thread(self.showTimedStatusMessage, ("package added",))
        except Exception, e:
            ow = OutputWindow(self.view.window())
            ow.write("Composer Error:\n\t" )
            ow.write("%s" % e)

