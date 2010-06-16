import hashlib
import urlparse
import urllib
import httplib
import socket
from cStringIO import StringIO

import replaylib


class RecordingHTTPResponse(httplib.HTTPResponse):

    def __init__(self, *args, **kwargs):
        httplib.HTTPResponse.__init__(self, *args, **kwargs)
        self.record_handle = None
        self._fp = self.fp

    def init_recording(self, req_hash):
        self.record_handle = replaylib.current.start_response(req_hash)
        self.record_handle.rec_start(self.version, self.status,
                                     self.reason, self.msg)
        self.fp = self

    def read(self, amt=None):
        try:
            self.fp = self._fp
            s = httplib.HTTPResponse.read(self, amt)
        finally:
            self.fp = self
        self.record_handle.rec_body(s)
        return s

    def close(self):
        try:
            self.fp = self._fp
            httplib.HTTPResponse.close(self)
        finally:
            self.fp = self

    def readline(self, *args, **kwargs):
        line = self._fp.readline(*args, **kwargs)
        self.record_handle.rec_body(line)
        return line

    def readlines(self, *args, **kwargs):
        lines = self._fp.readlines(*args, **kwargs)
        for l in lines:
            self.record_handle.rec_body(l)
        return lines


class RecordingHTTPRequest(object):

    def __init__(self, host, port):
        self.head_buffer = [host, str(port)]
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
        return hashlib.md5(req_head + req_body).digest()


_http_connection = httplib.HTTPConnection
_https_connection = httplib.HTTPSConnection


class RecordingHTTPConnection(_http_connection):

    def __init__(self, *args, **kwargs):
        _http_connection.__init__(self, *args, **kwargs)
        self.response_class = RecordingHTTPResponse
        self.req = RecordingHTTPRequest(self.host, self.port)
        self.sent_headers = False

    def _output(self, s):
        self.req.add_header(s)
        return _http_connection._output(self, s)

    def send(self, s):
        if self.sent_headers:
            self.req.add_body(s)

        assert self._HTTPConnection__state == httplib._CS_REQ_SENT
        self.sent_headers = True
        return _http_connection.send(self, s)

    def getresponse(self):
        req_hash = self.req.hash
        self.req.reset()

        r = _http_connection.getresponse(self)
        r.init_recording(req_hash)
        return r


class RecordingHTTPSConnection(RecordingHTTPConnection, _https_connection):
        default_port = httplib.HTTPS_PORT

        def __init__(self, host, port=None, key_file=None, cert_file=None,
                     strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
            RecordingHTTPConnection.__init__(self, host, port, strict, timeout)
            self.key_file = key_file
            self.cert_file = cert_file

        connect = _https_connection.connect


class PlayingHTTPConnection(_http_connection):

    def __init__(self, *args, **kwargs):
        _http_connection.__init__(self, *args, **kwargs)
        self.req = RecordingHTTPRequest(self.host, self.port)

    def connect(self):
        return

    def _output(self, s):
        self.req.add_header(s)

    def _send_output(self):
        return

    def send(self, s):
        assert self._HTTPConnection__state == httplib._CS_REQ_SENT
        self.req.add_body(s)

    def getresponse(self):
        req_hash = self.req.hash
        self.req.reset()
        
        try:
            resp_data = replaylib.current.get_next_response(req_hash)
        except IndexError:
            raise replaylib.UnknownRequestError(u"Received a request which "
                                                u"has not been recorded.")
        return PlayingHTTPResponse(resp_data)


class PlayingHTTPSConnection(PlayingHTTPConnection):
    default_port = httplib.HTTPS_PORT

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        PlayingHTTPConnection.__init__(self, host, port, strict, timeout)
        self.key_file = key_file
        self.cert_file = cert_file


class PlayingHTTPResponse(object):

    def __init__(self, r):
        self.version = r.version
        self.status = r.status
        self.reason = r.reason
        self.msg = r.headers
        assert self.msg is not None

        self.body = StringIO(r.body)
        self.fp = self.body

    def getheader(self, name, default=None):
        return self.msg.getheader(name, default)

    def getheaders(self):
        """Return list of (header, value) tuples."""
        return self.msg.items()

    def read(self, amt=None):
        if amt is None:
            return self.body.read()
        return self.body.read(amt)
