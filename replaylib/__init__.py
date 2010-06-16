import httplib
import pickle

from .data import ReplayData
from .stubs import (RecordingHTTPConnection,
                    RecordingHTTPSConnection,
                    PlayingHTTPConnection,
                    PlayingHTTPSConnection)


__version__ = '0.1'

current = None
record = False
playback = False
_HTTPConnection = httplib.HTTPConnection
_HTTPSConnection = httplib.HTTPSConnection


class StateError(Exception):
    pass


class UnknownRequestError(Exception):
    pass


def install(http, https):
    httplib.HTTPConnection = httplib.HTTP._connection_class = http
    httplib.HTTPSConnection = httplib.HTTPS._connection_class = https


def reset():
    global current, playback, record
    httplib.HTTPConnection = httplib.HTTP._connection_class = _HTTPConnection
    httplib.HTTPSConnection = httplib.HTTPS._connection_class = \
            _HTTPSConnection
    current = None
    playback = False
    record = False


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
    install(RecordingHTTPConnection, RecordingHTTPSConnection)


def stop_record_obj():
    global record, current
    if not record:
        raise StateError("Not currently recording.")
    copy = current
    reset()
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
    current, playback = obj, True
    install(PlayingHTTPConnection, PlayingHTTPSConnection)


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
    global playback
    if not playback:
        raise StateError("Not currently playing back.")
    reset()
