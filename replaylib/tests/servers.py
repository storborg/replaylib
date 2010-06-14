import os.path
import socket

from SocketServer import BaseServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

try:
    from OpenSSL import SSL
except ImportError:
    SSL = None

__here__ = os.path.dirname(__file__)

# Port number to use for reference webserver.
PORT = 9124
SECURE_PORT = PORT + 1

# Private key and certificate file to use for SSL testing.
TEST_CERT = os.path.join(__here__, 'host.pem')


class ReferenceServer(Thread):

    def __init__(self, port, server_class, secure):
        Thread.__init__(self)
        self.port = port
        self.counter = 0
        self.server_class = server_class

        class _Handler(BaseHTTPRequestHandler):

            def do_GET(s):
                self.counter += 1
                s.send_response(200)
                s.send_header('Content-type', 'text/plain')
                s.end_headers()
                resp = '%d requests to %s' % (self.counter, s.path)
                s.wfile.write(resp)

            def do_POST(s):
                self.counter += 1
                s.send_response(200)
                s.send_header('Content-type', 'text/plain')
                s.end_headers()
                content_length = s.headers.getheader('Content-length')
                if content_length:
                    body = s.rfile.read(int(content_length))
                else:
                    body = ''
                resp = '%d reqs to %s with %s' % (self.counter, s.path, body)
                s.wfile.write(resp)

            def log_message(s, *args):
                pass

            if secure:

                def setup(s):
                    s.connection = s.request
                    s.rfile = socket._fileobject(s.request, 'rb', s.rbufsize)
                    s.wfile = socket._fileobject(s.request, 'rb', s.wbufsize)

        self.handler = _Handler

    def run(self):
        httpd = self.server_class(('localhost', self.port), self.handler)
        httpd.serve_forever()


http_server = ReferenceServer(PORT, HTTPServer, secure=False)
http_server.start()


if SSL:

    class SecureHTTPServer(HTTPServer):

        def __init__(self, server_address, HandlerClass):
            BaseServer.__init__(self, server_address, HandlerClass)
            ctx = SSL.Context(SSL.SSLv23_METHOD)
            ctx.use_privatekey_file(TEST_CERT)
            ctx.use_certificate_file(TEST_CERT)
            self.socket = SSL.Connection(ctx, socket.socket(
                self.address_family, self.socket_type))
            self.server_bind()
            self.server_activate()

    https_server = ReferenceServer(SECURE_PORT, SecureHTTPServer, secure=True)
    https_server.start()
