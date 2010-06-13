import httplib


record = False
playback = False


class StateError(Exception):
    pass


def start_record(fname):
    """
    Install an httplib wrapper that records but does not modify calls.
    """
    global record, playback
    if record:
        raise StateError("Already recording.")
    if playback:
        raise StateError("Currently playing back.")
    record = True


def stop_record():
    """
    Close the current recording and return httplib to its normal state.
    """
    global record
    if not record:
        raise StateError("Not currently recording.")
    record = False


def start_playback(fname):
    """
    Install an httplib wrapper that intercepts calls and returns response as
    based on the recording being played back from.
    """
    global record, playback
    if record:
        raise StateError("Currently recording.")
    if playback:
        raise StateError("Already playing back.")


def stop_playback():
    """
    Stop intercepting calls and return httplib to its normal state.
    """
    global playback
    if not playback:
        raise StateError("Not currently playing back.")
