from unittest import TestCase
import replaylib


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

    def test_full(self):
        replaylib.start_record()

        # Do some httplib or urllib shit here.

        replaylib.stop_record('/tmp/replaylib-test.pkl')

        replaylib.start_playback('/tmp/replaylib-test.pkl')

        # Do the same httplib shit again.

        replaylib.stop_playback()
