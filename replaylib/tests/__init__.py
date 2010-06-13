from unittest import TestCase
import replaylib


class StateTest(TestCase):
    
    def test_already_recording(self):
        replaylib.start_record('somefile.pkl')
        try:
            replaylib.start_record('blah.pkl')
        except replaylib.StateError:
            pass
        else:
            raise AssertionError("trying to record twice should fail")
