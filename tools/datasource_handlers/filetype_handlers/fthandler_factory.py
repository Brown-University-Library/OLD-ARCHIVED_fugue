from pathlib import Path
from importlib import import_module
from inspect import getmembers, isclass
from ._filetypehandler_abstract import Abstract_FileHandler
from abc import ABCMeta

THIS_DIR = Path(__file__).parent

#TODO: Also look somewhere local, not just in the module's directory.
class FTHandler_Factory():
    handlers = {}
    default = None

    def __init__(self):
        for fl in THIS_DIR.glob('*.py'):
            mod = fl.stem
            if not mod.startswith('_') and mod != 'fthandler_factory':
                mod = import_module('tools.datasource_handlers.filetype_handlers.'+mod)
                for name, obj in getmembers(mod, isclass):
                    try:
                        for mt in obj.mimetypes():
                            self.handlers[mt] = obj
                        if obj.default():
                            self.default = obj
                    except:
                        pass
        
    def build(self, mimetype):
        return self.handlers.get(mimetype, self.default)