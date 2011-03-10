from bdb import Bdb
import fud.tornado_server

class Fud(Bdb):

    @classmethod
    def instance(cls):
        try:
            return cls._fud_instance
        except AttributeError:
            instance = cls()
            cls._fud_instance = instance
            return instance

    def set_trace(self, frame=None):
        print 'in set_trace'
        Bdb.set_trace(self, frame)

    def user_line(self, frame):
        fud.tornado_server.enqueue_frame(frame)
        Bdb.user_line(self, frame)
        print 'enqueued'
