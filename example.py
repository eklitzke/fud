from functools import wraps
import datetime
import logging
import json

import tornado.ioloop
import tornado.httpserver
import tornado.web

import fud

logging.getLogger('').setLevel(logging.DEBUG)

class HomeHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("""
<html>
  <head>
    <title>Sample App</title>
    <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.5.0/jquery.min.js"></script>
  </head>
  <body>
    The current time is: <span id="current_time"></span>
  </body>
  <script type="text/javascript">
    $(document).ready(function () {
      setInterval(function () {
        $.get('/time', function (data) {
          $('#current_time').text(data.time);
        });
      }, 1000);
    });
  </script>
</html>""")

class TimeHandler(tornado.web.RequestHandler):

    def get(self):
        print 'handler for /time'
        fud.set_trace()
        now = datetime.datetime.now()
        time_str = now.strftime('%Y-%m-%d %H:%M:%S.') + '%03d' % (now.microsecond / 1000.0,)
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps({'time': time_str}))

def main(port=8888):
    fud.initialize()
    application = tornado.web.Application([
            ('/', HomeHandler),
            ('/time', TimeHandler)])

    io_loop = tornado.ioloop.IOLoop()
    http_server = tornado.httpserver.HTTPServer(application, io_loop=io_loop)
    http_server.listen(port)
    print 'main io_loop is %r' % (io_loop,)
    io_loop.start()

if __name__ == '__main__':
    main()
