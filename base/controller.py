from ConfigParser import ConfigParser

class Controller():
    def __init__(self, config_file, log_name=None, debug=False):
        self.config_file = config_file
        self.config = ConfigParser()
        self.config.read(self.config_file)
        self.debug = debug
        self.log = None