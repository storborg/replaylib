import hashlib
import urlparse
import urllib
import httplib
from cStringIO import StringIO

import replaylib

class RecordingHTTPResponse(httplib.HTTPResponse):
    def __init__(self, *args, **kwargs):
        httplib.HTTPResponse.__init__(self, *args, **kwargs)
        self.record_handle = None

    def init_recording(self, req_hash):
        self.record_handle = replaylib.current.start_response(req_hash)
        self.record_handle.rec_start(self.version, self.status, self.reason, self.msg)
    
    def read(self, amt):
        s = httplib.HTTPResponse.read(self, amt)
        self.record_handle.rec_body(s)
        return s


class RecordingHTTPRequest(object):
    def __init__(self):
        self.head_buffer = []
        self.body_buffer = []
        self.response_class = RecordingHTTPResponse

    def add_header(self, s):
        self.head_buffer.append(s)

    def add_body(self, s):
        self.body_buffer.append(s)

    def reset(self):
        del self.head_buffer[:]
        del self.body_buffer[:]

    @property
    def hash(self):
        req_head = "\r\n".join(sorted(self.head_buffer))
        req_body = "".join(self.body_buffer)
        if req_head.find("application/x-www-form-urlencoded") >= 0:
            body = sorted(urlparse.parse_qsl(req_body))
            req_body = urllib.urlencode(body)
        return hashlib.md5(req_head + req_body)
        

def recording_connection(base_class):
    state_attr = "_%s__state" % base_class.__name__
    
    class RecordingConnection(base_class):
        def __init__(self, *args, **kwargs):
            base_class.__init__(self, *args, **kwargs)
            self.response_class = RecordingHTTPResponse
            self.req = RecordingHTTPRequest()

        def _output(self, s):
            self.req.add_header(s)
            return base_class._output(self, s)

        def send(self, s):
            if getattr(self, state_attr) == httplib._CS_REQ_SENT:
                self.req.add_body(s)
            return base_class.send(self, s)

        def getresponse(self):
            req_hash = self.req.hash
            self.req.reset()

            r = base_class.getresponse(self)
            r.init_recording(req_hash)
            return r
    return RecordingConnection


RecordingHTTPConnection = recording_connection(httplib.HTTPConnection)
RecordingHTTPSConnection = recording_connection(httplib.HTTPSConnection)


def playing_connection(base_class):
    state_attr = "_%s__state" % base_class.__name__

    class PlayingConnection(httplib.HTTPConnection):
        def __init__(self, *args, **kwargs):
            base_class.__init__(self, *args, **kwargs)
            self.req = RecordingHTTPRequest()

        def connect(self):
            return

        def _output(self, s):
            self.req.add_header(s)

        def _send_output(self):
            return

        def send(self, s):
            if getattr(self, state_attr) == httplib._CS_REQ_SENT:
                self.req.add_body(s)

        def getresponse(self):
            req_hash = self.req.hash
            self.req.reset()
            
            resp_data = replaylib.current.get_next_response(req_hash)
            return PlayingHTTPResponse(resp_data)
    return PlayingConnection
        
PlayingHTTPConnection = playing_connection(httplib.HTTPConnection)
PlayingHTTPSConnection = playing_connection(httplib.HTTPSConnection)


class PlayingHTTPResponse(object):
    def __init__(self, version, status, reason, msg, body):
        self.version = version
        self.status = status
        self.reason = reason
        self.msg = msg
        self.body = StringIO(body)
        
    def getheader(self, name, default=None):
        if self.msg is None:
            raise httplib.ResponseNotReady()
        return self.msg.getheader(name, default)

    def getheaders(self):
        """Return list of (header, value) tuples."""
        if self.msg is None:
            raise httplib.ResponseNotReady()
        return self.msg.items()

    def read(self, amt=None):
        return self.body.read(amt)
