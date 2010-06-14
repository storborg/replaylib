from unittest import TestCase
import replaylib
import urllib
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread


class ReferenceServer(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.counter = 0
        class _Handler(BaseHTTPRequestHandler):
            def do_GET(s):
                self.counter += 1
                s.send_response(200)
                s.send_header('Content-type', 'text/plain')
                s.end_headers()
                resp = '%d requests to %s' % (self.counter, s.path)
                print resp
                s.wfile.write(resp)
        self.handler = _Handler
        
    def run(self):
        httpd = HTTPServer(('localhost', 9000), self.handler)
        print "serving..."
        httpd.serve_forever()


class ReplayTest(TestCase):

    def tearDown(self):
        try:
            replaylib.stop_record_obj()
        except replaylib.StateError:
            pass
    
    def test_already_recording(self):
        replaylib.start_record()
        try:
            replaylib.start_record()
        except replaylib.StateError:
            pass
        else:
            raise AssertionError("trying to record twice should fail")

    def test_full_basic(self):
        replaylib.start_record()

        server = ReferenceServer()
        server.start()

        # Do some httplib or urllib shit here.
        webf = urllib.urlopen('http://localhost:9000')
        real_buf = webf.read()
        webf.close()

        data = replaylib.stop_record_obj()
        
        assert len(data.map) > 0

        replaylib.start_playback_obj(data)

        # Do the same httplib shit again.
        webf = urllib.urlopen('http://localhost:9000')
        fake_buf = webf.read()
        webf.close()

        replaylib.stop_playback()

        assert real_buf == fake_buf
