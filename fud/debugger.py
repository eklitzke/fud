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
        if 'bdb.py' in frame.f_code.co_filename:
            # roflcopter, major hack
            return

        Bdb.user_line(self, frame)
        
        # this sets the frame, and then blocks until the web frontend has
        # signalled that it's ok to continue
        fud.tornado_server.current_frame.set_frame(frame)
