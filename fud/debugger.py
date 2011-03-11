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
        Bdb.set_trace(self, frame)

    def user_line(self, frame):
        print 'in user_line'
        Bdb.user_line(self, frame)
        fud.tornado_server.current_frame.set_frame(frame)
        print 'exiting user_line'
        #fud.tornado_server.wait_frame()
