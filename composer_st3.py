import sys
import os
sys.path.append(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__))
    )
)

import sublime
import sublime_plugin
import threading

from st3.Prefs  import Prefs
import st3.Finder as Finder
import st3.System as System
import st3.Window as Window

#make sure to import our edit commands
from st3.Window import ComposerSt3WriteCommand

Prefs = Prefs()
def plugin_loaded():
    Prefs.load()


class BaseComposerCommand(sublime_plugin.TextCommand):
    def locateComposerJson(self):
        '''
            locates a composer.json file. we try to find the file starting from the place where file being edited is
            and we go up until we reach the root folder
        '''
        currentFile = self.view.file_name()
        if (None == currentFile):
            raise Exception('You need to safe your file file, otherwise I cannot locate composer.json')

        currentFolder = os.path.dirname(currentFile)
        fileToLocate = 'composer.json'
        finder = Finder.File(currentFolder, fileToLocate)

        return finder.upward()

    def switchWorkingDir(self, dir):
        os.chdir(dir)

    def prepareCommandList(self, binary, command, args):
        command = [binary, command]
        if (len(args) > 0) :
            command = command + args

        return  command

    def go (self, binary, command, args):
        self.binary = binary
        self.command = command
        self.args =args
        '''
            executes composer
        '''
        try:
            workingDir = self.locateComposerJson()
            self.switchWorkingDir(workingDir)
        except Exception as e:
            msg = "[ERROR] Composer.json not found\n\n {0}".format(e)
            sublime.error_message(msg)
            return

        outputWindow = Window.Panel(self.view.window())
        outputWindow.write("\n -- COMPOSER -- \n\n");
        cmd = self.prepareCommandList(
            binary  = self.binary,
            command = self.command,
            args    = self.args
        )

        print (cmd)

        worker = System.Exec(
            command      = cmd,
            workingDir   = workingDir,
            outputWindow = outputWindow,
            statusBar    =  None #statusMessage
        )

        worker.doWork()

    def is_visible(self):
        st_version = 2

        # Warn about out-dated versions of ST3
        if sublime.version() == '':
            st_version = 3
            print('Package Control: Please upgrade to Sublime Text 3 build 3012 or newer')

        elif int(sublime.version()) > 3000:
            st_version = 3

        if st_version == 2 :
            return False

        return True

    def is_enabled(self):
        # ensure the file is saved
        return self.view.file_name() != None and len(self.view.file_name()) > 0



class St3ComposerInstallCommand(BaseComposerCommand):
    def run(self, edit):
        bin  = Prefs.composerCommand
        cmd  = 'install'
        args = Prefs.composerInstallExtra

        self.go(bin, cmd, args)

class St3ComposerUpdateCommand(BaseComposerCommand):
    def run(self, edit):
        bin  = Prefs.composerCommand
        cmd  = 'update'
        args = Prefs.composerUpdateExtra

        self.go(bin, cmd, args)

class St3ComposerSelfUpdateCommand(BaseComposerCommand):
    def run(self, edit):
        bin  = Prefs.composerCommand
        cmd  = 'self-update'
        args = Prefs.composerSelfUpdateExtra

        self.go(bin, cmd, args)

class St3ComposerDumpAutoloadCommand(BaseComposerCommand):
    def run(self, edit):
        bin  = Prefs.composerCommand
        cmd  = 'dump-autoload'
        args = Prefs.composerDumpAutoloadExtra

        self.go(bin, cmd, args)

class St3ComposerValidateCommand(BaseComposerCommand):
    def run(self, edit):
        bin  = Prefs.composerCommand
        cmd  = 'validate'
        args = Prefs.composerValidateExtra

        self.go(bin, cmd, args)

class St3EditComposerFileCommand(BaseComposerCommand):
    def run(self, edit):
        composerJsonFile = os.path.join(self.locateComposerJson(), 'composer.json')
        self.view.window().open_file(composerJsonFile)

class St3ComposerAddPackageCommand(BaseComposerCommand):
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

            bin  = Prefs.composerCommand
            cmd  = 'require'
            args = ["%s:%s" %(name, version)] + Prefs.composerRequireExtra

            self.go(bin, cmd, args)

        except Exception as e:
            ow = OutputWindow(self.view.window())
            ow.write("Composer Error:\n\t" )
            ow.write("%s" % e)


