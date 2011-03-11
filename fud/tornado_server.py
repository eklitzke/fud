import os
import sys
import logging
import Queue as queue
import resource
import thread
import threading

import tornado.ioloop
import tornado.httpserver
import tornado.web
from fud.initialize import demand_initialize

try:
    import simplejson as json
except ImportError:
    import json

_handlers = []
_http_server = None
_http_lock = threading.Lock()
_frame_queue = queue.Queue(maxsize=1)
#_frame_queue = queue.Queue()

log = logging.getLogger('fud.tornado_server')

@demand_initialize
def enqueue_frame(f):
    print 'enqueueing frame'
    _frame_queue.put(f)

frame_lock = threading.Lock()
current_frame = None

class _CurrentFrame(object):

    def __init__(self):
        self._lock = thread.allocate_lock()
        self._current_frame = None

    def get_frame(self):
        # this is atomic, even though it doesn't look like it
        return self._current_frame

    def release(self):
        if self._lock.locked():
            self._current_frame = None
            self._lock.release()

    def set_frame(self, frame):
        self._lock.acquire()
        self._current_frame = frame

        # wait for the lock to be released by another thread
        self._lock.acquire()
        self._lock.release()

current_frame = _CurrentFrame()

class RequestHandlerType(type(tornado.web.RequestHandler)):

    def __init__(cls, name, bases, cls_dict):
        _handlers.append(cls)

class RequestHandler(tornado.web.RequestHandler):

    __metaclass__ = RequestHandlerType

    def initialize(self):
        super(RequestHandler, self).initialize()
        self.env = {}

    def render_json(self, data={}):
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(data))

    def render(self, template_name, **extra):
        self.env.update(extra)
        super(RequestHandler, self).render(template_name, **self.env)

class InitializeHandler(RequestHandler):

    path = '/init'

    def get(self):
        self.env['pid'] = os.getpid()
        self.env['process_cmd'] = open('/proc/self/cmdline').read().replace('\0', ' ').strip()
        self.env['running_threads'] = threading.enumerate()
        self.render('init.html')

class ResourceHandler(RequestHandler):
    """Returns data about current memory/CPU resources"""

    path = '/resources'

    def get(self):
        mb_size = float(1<<20)
        fields = ['virt', 'res', 'shr', 'trs', 'drs', 'lrs', 'dt']
        pagesize = resource.getpagesize()
        data = open('/proc/self/statm').read().strip()
        memory = dict((k, int(v) * pagesize / mb_size) for k, v in zip(fields, data.split()))

        rusage = resource.getrusage(resource.RUSAGE_SELF)
        rusage_dict = dict((k, getattr(rusage, k)) for k in rusage.__class__.__dict__.iterkeys() if k.startswith('ru_'))
        return self.render_json({'memory': memory, 'rusage': rusage_dict})

class FramePoller(RequestHandler):

    path = '/poll_frame_queue'

    def get(self):
        frame = current_frame._current_frame # yep, this is atomic
        if frame is not None:
            self.render_json({'stopped': True,
                              'co_filename': frame.f_code.co_filename,
                              'f_lineno': frame.f_lineno})
        else:
            self.render_json({'stopped': False})

class Continue(RequestHandler):

    path = '/continue'

    def post(self):
        from fud.debugger import Fud
        Fud.instance().set_continue()
        current_frame.release()
        self.render_json({'status': 'ok'})

def get_server(io_loop, **kw):
    global _http_server

    try:
        _http_lock.acquire()

        if _http_server is None:
            log.info('creating tornado http server')
            port = kw.pop('port', 8080)

            kw.setdefault('debug', True)
            kw.setdefault('template_path', '/home/evan/code/fud/fud/templates')
            kw.setdefault('static_path', '/home/evan/code/fud/fud/static')

            routes = [(h.path, h) for h in _handlers if getattr(h, 'path', None)]
            app = tornado.web.Application(routes, **kw)

            _http_server = tornado.httpserver.HTTPServer(app, io_loop=io_loop)
            _http_server.listen(port)
    finally:
        _http_lock.release()

    return _http_server
