import sublime_plugin
import sublime

class ComposerSt3WriteCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        self.view.insert(edit, self.view.size(), kwargs['data'])

class ClearCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        self.view.replace(edit, sublime.Region(0,9999999999),'')

class Panel(object):
    def __init__(self, window, name = 'composer'):
        print ('init')
        self.window       = window
        self.name         = name
        self.outputWindow = None
        self.enabled      = 1

    def setEnabled(self, bool):
        self.enabled = bool


    def getOutputWindow(self):
        if (None is self.outputWindow):
            print ('creating output panel')
            self.outputWindow = self.window.create_output_panel(self.name)
            # self.clear()

        return self.outputWindow

    def show(self):
        if self.enabled is False:
            return

        self.getOutputWindow()
        self.window.run_command("show_panel", {"panel": "output." + self.name})

    def clear(self):
        # if (None is self.outputWindow):
        #     return

        # self.outputWindow.run_command('clear')
        # # outputWindow = self.getOutputWindow()
        # # outputWindow.set_read_only(False)
        # # edit = outputWindow.begin_edit()
        # # outputWindow.erase(edit, sublime.Region(0, outputWindow.size()))
        # # outputWindow.end_edit(edit)
        # # outputWindow.set_read_only(True)
        pass


    def write(self, data):
        print ('writting data')
        try:
            str = data.decode("utf-8")
            str = str.replace('\r\n', '\n').replace('\r', '\n')
        except :
            str = data

            print (str)
        # print (data)
        # return
        self.show()
        self.outputWindow.set_read_only(False)
        self.outputWindow.run_command('composer_st3_write', {'data': str})
        self.outputWindow.set_read_only(True)
        # if self.enabled is False :
        #     return

        # try:
        #     str = data.decode("utf-8")
        # except Exception :
        #     str = data
        # str = str.replace('\r\n', '\n').replace('\r', '\n')
        # outputWindow = self.getOutputWindow()
        # self.show()

        # # selection_was_at_end = (len(self.output_view.sel()) == 1
        # #  and self.output_view.sel()[0]
        # #    == sublime.Region(self.output_view.size()))
        # self.outputWindow.set_read_only(False)
        # edit = outputWindow.begin_edit()
        # outputWindow.insert(edit, outputWindow.size(), str)
        # #if selection_was_at_end:
        # outputWindow.show(outputWindow.size())
        # outputWindow.end_edit(edit)
        # outputWindow.set_read_only(True)
