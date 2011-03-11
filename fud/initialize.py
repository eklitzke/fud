from functools import wraps
import sys
import time
import thread
import threading
import tornado.ioloop

_thread_lock = thread.allocate_lock()
thread_id = None

class TornadoThread(threading.Thread):

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.daemon = True

    def run(self):
        # n.b. always get a new io loop, don't use IOLoop.instance()
        import fud.tornado_server
        io_loop = tornado.ioloop.IOLoop()
        http_server = fud.tornado_server.get_server(io_loop, port=self.port)
        try:
            print 'starting fud i/o loop'
            io_loop.start()
        finally:
            print 'fud i/o loop stopped'

def initialize(port=8777):
    global thread_id
    with _thread_lock:
        if thread_id is None:
            print 'fud.initialize.initialize'
            tornado_thread = TornadoThread(port)
            tornado_thread.start()
            thread_id = tornado_thread.ident
            print 'done starting new thread, thread was %s, threads are: %s' % (thread_id, threading.enumerate())

def demand_initialize(func):
    @wraps(func)
    def inner(*args, **kwargs):
        initialize()
        return func(*args, **kwargs)
    return inner

