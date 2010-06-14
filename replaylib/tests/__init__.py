from unittest import TestCase
import urllib
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import replaylib

# Port number to use for reference webserver.
PORT = 9000


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
        httpd = HTTPServer(('localhost', PORT), self.handler)
        print "serving..."
        httpd.serve_forever()


class ReplayFunctionalityTest(TestCase):

    def test_single(self):
        replaylib.start_record()

        server = ReferenceServer()
        server.start()

        # Do some httplib or urllib shit here.
        webf = urllib.urlopen('http://localhost:%d' % PORT)
        real_buf = webf.read()
        webf.close()

        data = replaylib.stop_record_obj()
        
        assert len(data.map) > 0

        replaylib.start_playback_obj(data)

        # Do the same httplib shit again.
        webf = urllib.urlopen('http://localhost:%d' % PORT)
        fake_buf = webf.read()
        webf.close()

        replaylib.stop_playback()

        assert real_buf == fake_buf


class ReplayStateTest(TestCase):

    def setUp(self):
        replaylib.reset()

    def test_already_recording(self):
        replaylib.start_record()
        try:
            replaylib.start_record()
        except replaylib.StateError:
            pass
        else:
            raise AssertionError("record twice should fail")

    def test_stop_not_recording(self):
        try:
            replaylib.stop_record_obj()
        except replaylib.StateError:
            pass
        else:
            raise AssertionError("stop recording without start should fail")

    def test_already_playing(self):
        replaylib.start_playback_obj(replaylib.ReplayData())
        try:
            replaylib.start_playback_obj(replaylib.ReplayData())
        except replaylib.StateError:
            pass
        else:
            raise AssertionError("playback twice should fail")

    def test_stop_not_playing(self):
        try:
            replaylib.stop_playback()
        except replaylib.StateError:
            pass
        else:
            raise AssertionError("stop playback without start should fail")

    def test_playback_while_recording(self):
        replaylib.start_record()
        try:
            replaylib.start_playback_obj(replaylib.ReplayData())
        except replaylib.StateError:
            pass
        else:
            raise AssertionError("playback during recording should fail")

    def test_record_while_playback(self):
        replaylib.start_playback_obj(replaylib.ReplayData())
        try:
            replaylib.start_record()
        except replaylib.StateError:
            pass
        else:
            raise AssertionError("record during playback should fail")
