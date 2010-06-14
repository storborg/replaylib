import hashlib
import urlparse
import urllib
import httplib

import replaylib


class RecordingHTTPResponse(httplib.HTTPResponse):
    def __init__(self):
        self.record_handle = replaylib.current.start_response(self.hash)

    def begin(self):
        httplib.HTTPConnection.begin()
        self.record_handle.rec_start(self, self.version, self.status, self.reason, self.msg.dict)

    def read(self, amt):
        s = httplib.HTTPConnection.read(amt)
        self.record_handle.rec_body(s)
        return s
        

class RecordingHTTPConnection(httplib.HTTPConnection):
    def __init__(self):
        self.head_buffer = []
        self.body_buffer = []
        self.response_class = RecordingHTTPResponse

    def _output(self, s):
        self.head_buffer.append(s)
        return httplib.HTTPConnection._output(s)

    def send(self, s):
        self.body_buffer.append(s)
        return httplib.HTTPConnection.send(s)

    def getresponse(self):
        req_head = "\r\n".join(sorted(self.head_buffer))
        if req_head.find("application/x-www-form-urlencoded") >= 0:
            body = sorted(urlparse.parse_qsl(self.body_buffer))
            req_body = urllib.urlencode(body)
        else:
            req_body = "".join(self.body_buffer)
        req_hash = hashlib.md5(req_head + req_body)

        r = httplib.HTTPConnection.getresponse()
        r.hash = req_hash
        return r
