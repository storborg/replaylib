import sys

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


server = ReferenceServer()
server.start()


class ReplayFunctionalityTest(TestCase):

    def tearDown(self):
        replaylib.reset()

    def _grab(self, path=''):
        sys.stderr.write("doing grab [%s]\n" % path)
        webf = urllib.urlopen('http://localhost:%d/%s' % (PORT, path))
        buf = webf.read()
        webf.close()
        sys.stderr.write("done\n")
        return buf

    def _with_actions(self, func):
        replaylib.start_record()
        real_compare = func()
        data = replaylib.stop_record_obj()

        assert len(data.map) > 0

        replaylib.start_playback_obj(data)
        fake_compare = func()
        replaylib.stop_playback()

        assert real_compare == fake_compare

    def test_single(self):
        def func():
            return self._grab()
        self._with_actions(func)

    def test_multiple(self):
        def func():
            ret = []
            ret.append(self._grab())
            ret.append(self._grab())
            return ret
        self._with_actions(func)

    def test_different_single(self):
        def func():
            ret = []
            ret.append(self._grab('foo'))
            ret.append(self._grab('bar'))
            return ret
        self._with_actions(func)

    def test_different_multiple(self):
        def func():
            ret = []
            ret.append(self._grab('foo'))
            ret.append(self._grab('bar'))
            ret.append(self._grab('foo'))
            ret.append(self._grab('baz'))
        self._with_actions(func)


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
