##
## REST Mock Framework
##
## Max Kuznetsov <max@ngti.nl> 2014
##

import urlparse
import BaseHTTPServer

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def process(self):
        self.parsed_url = urlparse.urlparse(self.path)
        self.query_params = urlparse.parse_qs(self.parsed_url.query)

        try:
            length = int(self.headers['Content-Length'])

            self.body = self.rfile.read(length)
        except Exception:
            self.body = ""

        # Iterate over actions to find first match
        for action in self.server.actions:
            if action(self):
               self.send_response(action.response_code, "")
               self.end_headers()
               self.wfile.write(self.substitute_body(action.response_body))

               return

        self.send_response(404, "")
        self.end_headers()
        self.wfile.write("")

    do_GET = process
    do_POST = process
    do_PUT = process
    do_DELETE = process

    def substitute_body(self, body):
        """
        Substitute some dynamic data in response body
        """

        for param, val in self.query_params.iteritems():
            body = body.replace("${%s}" % param, val[0])

        return body

def serve(actions, port=8000, ip=''):
    """
    Run HTTP server
    """

    address = (ip, port)

    srv = BaseHTTPServer.HTTPServer(address, Handler)
    srv.actions = actions

    srv.serve_forever()
