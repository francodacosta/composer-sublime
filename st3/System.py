import threading
import subprocess
import sublime
import os
import functools

class Exec(object):

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

        print (self.command)
        self.appendData("executing: %s\n" % ' '.join(self.command))

        try:
            self.proc = subprocess.Popen(
                self.command,
                shell  = shell,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                cwd    = self.workingDir
            )

            print ('process created')

            if self.proc.stdout:
                threading.Thread(target = self.readStdOut).start()
            if self.proc.stderr:
                threading.Thread(target = self.readStdErr).start()

        except Exception as e:
            msg = "Error: %s" % e
            print(msg)
            self.appendData(msg)
            self.statusBar.stop = True
            self.statusBar.error = True
            # self.stopStatusProgress()
            # thread.start_new_thread(self.statusBar.timedMessage,(msg))

    def appendData(self, data):
        if self.outputWindow is None:
            print("Skipping output window messages")
            return
        self.counter = self.counter + 1
        self.outputWindow.window.active_view().set_status("Composer", "%s" % self.counter)
        self.outputWindow.write(data)

    def startStatusProgress(self):
        if self.statusBar is None:
            print("Skipping status bar messages")
            return
        self.statusBar.start()

    def stopStatusProgress(self):
        if self.statusBar is None:
            print("Skipping status bar messages")
            return
        self.statusBar.stop = True
        # self.statusBar.clear()

    def readStdOut(self):
        while True:
            data = os.read(self.proc.stdout.fileno(), 2 ** 15)
            data = data.decode("utf-8")
            print (data)
            if "" == data :
                self.proc.stdout.close()
                self.appendData("\n-- Terminated -- \n")
                if self.statusBar is not None:
                    self.statusBar.stop = True
                break
            else:
                sublime.set_timeout(functools.partial(self.appendData, data), 0)

    def readStdErr(self):
        while True:
            data = os.read(self.proc.stderr.fileno(), 2 ** 15)
            data = data.decode("utf-8")
            if "" == data :
                self.proc.stderr.close()
                # self.appendData("\n--- Execution Finished ---")
                #
                break
            else:
                sublime.set_timeout(functools.partial(self.appendData, data), 0)
        pass
