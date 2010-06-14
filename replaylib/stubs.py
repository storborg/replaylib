import hashlib
import urlparse
import urllib
import httplib
from cStringIO import StringIO

import replaylib

def hash_request(header_lines, body_lines):
    req_head = "\r\n".join(sorted(header_lines))
    req_body = "".join(body_lines)
    if req_head.find("application/x-www-form-urlencoded") >= 0:
        body = sorted(urlparse.parse_qsl(req_body))
        req_body = urllib.urlencode(body)
    return hashlib.md5(req_head + req_body)
    

class RecordingHTTPResponse(httplib.HTTPResponse):
    def __init__(self):
        self.record_handle = replaylib.current.start_response(self.req_hash)

    def begin(self):
        httplib.HTTPConnection.begin()
        self.record_handle.rec_start(self.version, self.status, self.reason, self.msg)

    def read(self, amt):
        s = httplib.HTTPConnection.read(amt)
        self.record_handle.rec_body(s)
        return s
        

class RecordingHTTPConnection(httplib.HTTPConnection):
    def __init__(self, *args, **kwargs):
        httplib.HTTPConnection.__init__(self, *args, **kwargs)
        self.head_buffer = []
        self.body_buffer = []
        self.response_class = RecordingHTTPResponse

    def _output(self, s):
        self.head_buffer.append(s)
        return httplib.HTTPConnection._output(self, s)

    def send(self, s):
        if self.__state == httplib._CS_REQ_SENT:
            self.body_buffer.append(s)
        return httplib.HTTPConnection.send(self, s)

    def getresponse(self):
        req_hash = hash_request(self.head_buffer, self.body_buffer)
        del self.head_buffer[:]
        del self.body_buffer[:]
        
        r = httplib.HTTPConnection.getresponse(self)
        r.hash = req_hash
        return r
    

class PlayingHTTPConnection(httplib.HTTPConnection):
    def connect(self):
        return
    
    def _output(self, s):
        self.head_buffer.append(s)
        
    def _send_output(self):
        return

    def send(self, s):
        if self.__state == httplib._CS_REQ_SENT:
            self.body_buffer.append(s)

    def getresponse(self):
        req_hash = self._current_hash()
        resp_data = replaylib.current.get_next_response(req_hash)
        return PlayingHTTPResponse(resp_data)

    
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
