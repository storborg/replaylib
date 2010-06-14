import httplib
import pickle

from .data import ReplayData

current = None
record = False
playback = False


class StateError(Exception):
    pass


def start_record():
    """
    Install an httplib wrapper that records but does not modify calls.
    """
    global record, playback, current
    if record:
        raise StateError("Already recording.")
    if playback:
        raise StateError("Currently playing back.")
    record = True
    current = ReplayData()

    # Install recording httplib stub.


def stop_record_obj():
    global record, current
    if not record:
        raise StateError("Not currently recording.")
    record = False
    copy, current = current, None

    # Return httplib to original state.

    return copy


def stop_record(fname):
    """
    Close the current recording, return httplib to its normal state, and save
    the recording to fname.
    """
    with open(fname, 'w') as f:
        pickle.dump(stop_record_obj(), f)


def start_playback_obj(obj):
    global record, playback, current
    if record:
        raise StateError("Currently recording.")
    if playback:
        raise StateError("Already playing back.")
    playback = True

    # Install playback httplib stub.


def start_playback(fname):
    """
    Install an httplib wrapper that intercepts calls and returns response as
    based on the recording being played back from.
    """
    with open(fname, 'r') as f:
        start_playback_obj(pickle.load(f))


def stop_playback():
    """
    Stop intercepting calls and return httplib to its normal state.
    """
    global playback, current
    if not playback:
        raise StateError("Not currently playing back.")
    current = None

    # Return httplib to original state.
