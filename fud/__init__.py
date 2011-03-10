from functools import wraps
import tornado.ioloop
import sys
import thread

import fud.tornado_server
from fud.debugger import Fud
from fud.initialize import *

@demand_initialize
def set_trace():
    print 'set_trace called'
    return Fud.instance().set_trace(sys._getframe().f_back)

__all__ = ['start_debugger', 'set_break', 'Fud']
