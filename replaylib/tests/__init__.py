from unittest import TestCase
import replaylib
import urllib


class ReplayTest(TestCase):

    def tearDown(self):
        try:
            replaylib.stop_record('/tmp/trash.pkl')
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

        # Do some httplib or urllib shit here.
        webf = urllib.urlopen('http://ip.crookedmedia.com')
        real_buf = webf.read()
        webf.close()

        data = replaylib.stop_record_obj()
        
        assert len(data.map) > 0

        replaylib.start_playback_obj(data)

        # Do the same httplib shit again.
        webf = urllib.urlopen('http://ip.crookedmedia.com')
        fake_buf = webf.read()
        webf.close()

        replaylib.stop_playback()

        assert real_buf == fake_buf
