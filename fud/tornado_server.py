import os
import sys
import logging
import Queue as queue
import resource
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
#_frame_queue = queue.Queue(maxsize=1)
_frame_queue = queue.Queue()

log = logging.getLogger('fud.tornado_server')

@demand_initialize
def enqueue_frame(f):
    print 'enqueueing frame'
    _frame_queue.put(f)

frame_lock = threading.Lock()
current_frame = None

class _CurrentFrame(object):

    def __init__(self):
        self._frame_lock = threading.RLock()
        self._condition = threading.Condition(self._frame_lock)
        self._current_frame = None

    @property
    def current_frame(self):
        with self._frame_lock:
            return self._current_frame

    def release_frame(self):
        with self._frame_lock:
            self._current_frame = None
            self._condition.notify()

    def set_frame(self, f):
        with self._frame_lock:
            if self._current_frame is None:
                self._current_frame = f
                return

        while True:
            self._condition.wait()
            if self._current_frame is None:
                self._current_frame = f

            self._condition.wait()

class RequestHandlerType(type(tornado.web.RequestHandler)):

    def __init__(cls, name, bases, cls_dict):
        _handlers.append(cls)

class RequestHandler(tornado.web.RequestHandler):

    __metaclass__ = RequestHandlerType

    def __init__(self, *args, **kwargs):
        print 'initializing thingy'
        return super(RequestHandler, self).__init__(*args, **kwargs)

    def initialize(self):
        print 'RequestHandler -> in %s' % (self.__class__.__name__,)
        log.info('in %s' % (self.__class__.__name__,))
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
        print '/init being served'
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

    current_frame = None
    frame_lock = threading.Lock()

    def get(self):

        print >> sys.stderr, 'in frame poller'
        with self.frame_lock:
            frame = self.__class__.current_frame
            if frame is None:
                try:
                    frame = self.__class__.current_frame = _frame_queue.get(False)
                except queue.Empty:
                    self.__class__.current_frame = None

        print '-- /poll_frame_queue, frame = %r '% (frame,)
        if frame is not None:
            self.render_json({'stopped': True,
                              'co_filename': frame.f_code.co_filename,
                              'f_lineno': frame.f_lineno})
        else:
            self.render_json({'stopped': False})

def get_server(io_loop, **kw):
    global _http_server

    try:
        _http_lock.acquire()

        print 'fud io_loop is %r' % (io_loop,)
        if _http_server is None:
            log.info('creating tornado http server')
            port = kw.pop('port', 8080)

            kw.setdefault('debug', True)
            kw.setdefault('template_path', '/home/evan/code/fud/fud/templates')
            kw.setdefault('static_path', '/home/evan/code/fud/fud/static')

            routes = [(h.path, h) for h in _handlers if getattr(h, 'path', None)]
            print 'routes are %s' % (routes,)
            app = tornado.web.Application(routes, **kw)

            _http_server = tornado.httpserver.HTTPServer(app)
            print 'fud server listening on port %d' % (port,)
            _http_server.listen(port)
    finally:
        _http_lock.release()

    return _http_server
