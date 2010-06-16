from unittest import TestCase
from nose.plugins.skip import SkipTest

import urllib
import httplib

from . import servers

import replaylib

# Filename to use for pickle test.
TEST_FILENAME = '/tmp/replaylib-test.pkl'


class ReplayFunctionalityTest(TestCase):

    def tearDown(self):
        replaylib.reset()

    def _urlopen(self, path='', params=None):
        return urllib.urlopen('http://localhost:%d/%s' % (servers.PORT, path),
                              params)

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

    def test_playback_unknown_request(self):
        replaylib.start_record()
        real = self._grab()
        data = replaylib.stop_record_obj()
        replaylib.start_playback_obj(data)
        try:
            fake = self._grab(params='post data')
        except replaylib.UnknownRequestError:
            pass
        else:
            raise AssertionError("unknown request should fail")
        replaylib.stop_playback()

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
        conn = httplib.HTTPConnection('localhost:%d' % servers.PORT)
        conn.connect()
        conn.request("GET", "/")
        resp = conn.getresponse()
        real_body = resp.read()
        real_headers = resp.getheaders()
        conn.close()
        data = replaylib.stop_record_obj()

        replaylib.start_playback_obj(data)
        conn = httplib.HTTPConnection('localhost:%d' % servers.PORT)
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
        conn = httplib.HTTPConnection('localhost:%d' % servers.PORT)
        conn.request("GET", "/")
        resp = conn.getresponse()
        real = resp.getheader('Content-type')
        conn.close()
        data = replaylib.stop_record_obj()

        replaylib.start_playback_obj(data)
        conn = httplib.HTTPConnection('localhost:%d' % servers.PORT)
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
        conn = httplib.HTTPConnection('localhost:%d' % servers.PORT)
        conn.request("GET", "/")
        resp = conn.getresponse()
        real = resp.read(2)
        conn.close()
        data = replaylib.stop_record_obj()

        replaylib.start_playback_obj(data)
        conn = httplib.HTTPConnection('localhost:%d' % servers.PORT)
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



class ReplayFunctionalitySSLTest(TestCase):

    def tearDown(self):
        replaylib.reset()

    def test_single(self):
        if not servers.SSL:
            raise SkipTest
        replaylib.start_record()
        webf = urllib.urlopen('https://localhost:%d' % servers.SECURE_PORT)
        real_compare = webf.read()
        webf.close()
        data = replaylib.stop_record_obj()

        replaylib.start_playback_obj(data)
        webf = urllib.urlopen('https://localhost:%d' % servers.SECURE_PORT)
        fake_compare = webf.read()
        webf.close()
        replaylib.stop_playback()

        assert real_compare == fake_compare
