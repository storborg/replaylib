import sys
import os.path
import urllib
from unittest import TestCase, TestSuite
from nose.plugins import PluginTester

import replaylib

from . import servers

from replaylib.noseplugin import ReplayLibPlugin

compare = ''

TEST_FILENAME = '/tmp/replaylib-plugin.pkl'


class TestPluginRecording(PluginTester, TestCase):
    plugins = [ReplayLibPlugin()]
    activate = '--replaylib-record=%s' % TEST_FILENAME

    def makeSuite(self):

        class TC(TestCase):

            def runTest(self):
                global compare
                webf = urllib.urlopen('http://localhost:%d' % servers.PORT)
                compare = webf.read()
                webf.close()
                assert len(buf) > 0
        return TestSuite([TC()])

    def test_recording(self):
        replaylib.start_playback(TEST_FILENAME)
        webf = urllib.urlopen('http://localhost:%d' % servers.PORT)
        fake = webf.read()
        webf.close()
        replaylib.stop_playback()
        assert fake == compare


class TestPluginPlayback(PluginTester, TestCase):
    plugins = [ReplayLibPlugin()]
    activate = '--replaylib-playback=%s' % TEST_FILENAME

    def setUp(self):
        global compare
        replaylib.start_record()
        webf = urllib.urlopen('http://localhost:%d' % servers.PORT)
        compare = webf.read()
        webf.close()
        replaylib.stop_record(TEST_FILENAME)
        PluginTester.setUp(self)

    def makeSuite(self):

        class TC(TestCase):

            def runTest(self):
                global compare
                webf = urllib.urlopen('http://localhost:%d' % servers.PORT)
                fake = webf.read()
                webf.close()
                assert fake == compare
        return TestSuite([TC()])

    def test_okay(self):
        for line in self.output:
            if line.startswith('Ran 1 test'):
                ran_tests = True
            if line.strip() == 'OK':
                success = True
        assert ran_tests and success


class TestPluginDisabled(PluginTester, TestCase):
    plugins = [ReplayLibPlugin()]
    activate = ''

    def makeSuite(self):

        class TC(TestCase):

            def runTest(self):
                assert True
        return TestSuite([TC()])

    def test_okay(self):
        for line in self.output:
            if line.startswith('Ran 1 test'):
                ran_tests = True
            if line.strip() == 'OK':
                success = True
        assert ran_tests and success
