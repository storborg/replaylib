import httplib
import pickle

"""
Replay files will be stored as a pickled dict that looks like:

    {'<sha1 of canonicalized request data>': ['first response body',
                                              'second response body',
                                              'third response body',
                                              ...],
     '<sha1 of different request data>': ['first response body',
                                          'second response body']}
"""
current = {}

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

    # Install recording httplib stub.


def stop_record(fname):
    """
    Close the current recording, return httplib to its normal state, and save
    the recording to fname.
    """
    global record, current
    if not record:
        raise StateError("Not currently recording.")
    record = False

    with open(fname, 'w') as f:
        pickle.dump(current, f)
    current = {}

    # Return httplib to original state.


def start_playback(fname):
    """
    Install an httplib wrapper that intercepts calls and returns response as
    based on the recording being played back from.
    """
    global record, playback, current
    if record:
        raise StateError("Currently recording.")
    if playback:
        raise StateError("Already playing back.")
    playback = True

    with open(fname, 'r') as f:
        current = pickle.load(f)

    # Install playback httplib stub.


def stop_playback():
    """
    Stop intercepting calls and return httplib to its normal state.
    """
    global playback, current
    if not playback:
        raise StateError("Not currently playing back.")
    current = {}

    # Return httplib to original state.
