from unittest import TestCase

import os
import os.path
import urllib
import httplib
import socket

from SocketServer import BaseServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

try:
    from OpenSSL import SSL
except ImportError:
    SSL = None

import replaylib

__here__ = os.path.dirname(__file__)

# Port number to use for reference webserver.
PORT = 9000
SECURE_PORT = PORT + 1

# Filename to use for pickle test.
TEST_FILENAME = '/tmp/replaylib-test.pkl'

# Private key and certificate file to use for SSL testing.
TEST_CERT = os.path.join(__here__, 'host.pem')


class ReferenceServer(Thread):

    def __init__(self, port, server_class, secure):
        Thread.__init__(self)
        self.port = port
        self.counter = 0
        self.server_class = server_class

        class _Handler(BaseHTTPRequestHandler):

            def do_GET(s):
                self.counter += 1
                s.send_response(200)
                s.send_header('Content-type', 'text/plain')
                s.end_headers()
                resp = '%d requests to %s' % (self.counter, s.path)
                s.wfile.write(resp)

            def do_POST(s):
                self.counter += 1
                s.send_response(200)
                s.send_header('Content-type', 'text/plain')
                s.end_headers()
                content_length = s.headers.getheader('Content-length')
                if content_length:
                    body = s.rfile.read(int(content_length))
                else:
                    body = ''
                resp = '%d reqs to %s with %s' % (self.counter, s.path, body)
                s.wfile.write(resp)

            def log_message(s, *args):
                pass

            if secure:
                def setup(s):
                    s.connection = s.request
                    s.rfile = socket._fileobject(s.request, 'rb', s.rbufsize)
                    s.wfile = socket._fileobject(s.request, 'rb', s.wbufsize)

        self.handler = _Handler

    def run(self):
        httpd = self.server_class(('localhost', self.port), self.handler)
        httpd.serve_forever()


http_server = ReferenceServer(PORT, HTTPServer, secure=False)
http_server.start()


class ReplayFunctionalityTest(TestCase):

    def tearDown(self):
        replaylib.reset()

    def _urlopen(self, path='', params=None):
        return urllib.urlopen('http://localhost:%d/%s' % (PORT, path), params)

    def _grab(self, path='', params=None):
        webf = self._urlopen(path, params)
        buf = webf.read()
        webf.close()
        return buf

    def _with_actions(self, func):
        replaylib.start_record()
        real_compare = func()
        data = replaylib.stop_record_obj()

        replaylib.start_playback_obj(data)
        fake_compare = func()
        replaylib.stop_playback()

        assert real_compare == fake_compare

    def test_do_nothing(self):

        def func():
            return ''
        self._with_actions(func)

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

    def test_post_single(self):

        def func():
            params = 'post data'
            return self._grab('', params=params)
        self._with_actions(func)

    def test_with_file(self):
        replaylib.start_record()
        real = self._grab()
        replaylib.stop_record(TEST_FILENAME)
        replaylib.start_playback(TEST_FILENAME)
        fake = self._grab()
        replaylib.stop_playback()

        assert real == fake

    def test_readlines(self):
        replaylib.start_record()
        webf = self._urlopen()
        real = webf.readlines()
        webf.close()
        data = replaylib.stop_record_obj()
        replaylib.start_playback_obj(data)
        webf = self._urlopen()
        fake = webf.readlines()
        webf.close()
        replaylib.stop_playback()

    def test_readline(self):
        replaylib.start_record()
        webf = self._urlopen()
        real = webf.readline()
        webf.close()
        data = replaylib.stop_record_obj()
        replaylib.start_playback_obj(data)
        webf = self._urlopen()
        fake = webf.readline()
        webf.close()
        replaylib.stop_playback()

    def test_with_httplib(self):
        replaylib.start_record()
        conn = httplib.HTTPConnection('localhost:%d' % PORT)
        conn.connect()
        conn.request("GET", "/")
        resp = conn.getresponse()
        real_body = resp.read()
        real_headers = resp.getheaders()
        conn.close()
        data = replaylib.stop_record_obj()

        replaylib.start_playback_obj(data)
        conn = httplib.HTTPConnection('localhost:%d' % PORT)
        conn.connect()
        conn.request("GET", "/")
        resp = conn.getresponse()
        fake_body = resp.read()
        fake_headers = resp.getheaders()
        conn.close()
        replaylib.stop_playback()

        assert real_body == fake_body
        assert real_headers == fake_headers

    def test_getheader_with_httplib(self):
        replaylib.start_record()
        conn = httplib.HTTPConnection('localhost:%d' % PORT)
        conn.request("GET", "/")
        resp = conn.getresponse()
        real = resp.getheader('Content-type')
        conn.close()
        data = replaylib.stop_record_obj()

        replaylib.start_playback_obj(data)
        conn = httplib.HTTPConnection('localhost:%d' % PORT)
        conn.request("GET", "/")
        resp = conn.getresponse()
        fake = resp.getheader('Content-type')
        conn.close()
        replaylib.stop_playback()

        assert real == fake

    def test_content_type_header(self):
        replaylib.start_record()
        webf = self._urlopen()
        real = webf.info().getheader('Content-type')
        webf.close()
        data = replaylib.stop_record_obj()
        replaylib.start_playback_obj(data)
        webf = self._urlopen()
        fake = webf.info().getheader('Content-type')
        webf.close()
        replaylib.stop_playback()

    def test_read_partial(self):
        replaylib.start_record()
        conn = httplib.HTTPConnection('localhost:%d' % PORT)
        conn.request("GET", "/")
        resp = conn.getresponse()
        real = resp.read(2)
        conn.close()
        data = replaylib.stop_record_obj()

        replaylib.start_playback_obj(data)
        conn = httplib.HTTPConnection('localhost:%d' % PORT)
        conn.request("GET", "/")
        resp = conn.getresponse()
        fake = resp.read(2)
        conn.close()
        replaylib.stop_playback()

        assert real == fake


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


if SSL:
    class SecureHTTPServer(HTTPServer):
        def __init__(self, server_address, HandlerClass):
            BaseServer.__init__(self, server_address, HandlerClass)
            ctx = SSL.Context(SSL.SSLv23_METHOD)
            ctx.use_privatekey_file (TEST_CERT)
            ctx.use_certificate_file(TEST_CERT)
            self.socket = SSL.Connection(ctx, socket.socket(self.address_family,
                                                            self.socket_type))
            self.server_bind()
            self.server_activate()

    https_server = ReferenceServer(SECURE_PORT, SecureHTTPServer, secure=True)
    https_server.start()

    class ReplayFunctionalitySSLTest(TestCase):

        def tearDown(self):
            replaylib.reset()

        def test_single(self):
            replaylib.start_record()
            webf = urllib.urlopen('https://localhost:%d' % SECURE_PORT)
            real_compare = webf.read()
            webf.close()
            data = replaylib.stop_record_obj()

            replaylib.start_playback_obj(data)
            webf = urllib.urlopen('https://localhost:%d' % SECURE_PORT)
            fake_compare = webf.read()
            webf.close()
            replaylib.stop_playback()

            assert real_compare == fake_compare
