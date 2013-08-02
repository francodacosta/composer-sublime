import sublime

class Prefs(object):
    """
        Plugin preferences
    """

    # @staticmethod
    def load(self):
        settings = sublime.load_settings('composer-sublime.sublime-settings')

        print ('---------',settings, '----------')

        self.debug                     = settings.get('show_debug', 1)
        self.showOutput                = settings.get('show_output')
        self.showStatus                = settings.get('show_status')

        self.composerCommand           = settings.get('composer_command')
        self.composerFile              = settings.get('composer_file', 'composer.json')

        self.composerInstallExtra      = settings.get('composer_install_extra')
        self.composerUpdateExtra       = settings.get('composer_update_extra')
        self.composerSelfUpdateExtra   = settings.get('composer_selfupdate_extra')
        self.composerRequireExtra      = settings.get('composer_require_extra')
        self.composerDumpAutoloadExtra = settings.get('composer_dumpautoload_extra')
        self.composerValidateExtra     = settings.get('composer_validate_extra')


        print(self.debug                     )
        print(self.showOutput                )
        print(self.showStatus                )

        print(self.composerCommand           )
        print(self.composerFile              )

        print(self.composerInstallExtra      )
        print(self.composerUpdateExtra       )
        print(self.composerSelfUpdateExtra   )
        print(self.composerRequireExtra      )
        print(self.composerDumpAutoloadExtra )
        print(self.composerValidateExtra     )
