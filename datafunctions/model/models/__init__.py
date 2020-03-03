#  Slightly hacky way to import all local files
#  Courtesy of: https://stackoverflow.com/a/1057534/12706019
from os.path import dirname, basename, isfile, join
import glob
modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
#  This lets us import the module and have the local files as submodules
from datafunctions.model.models import *
