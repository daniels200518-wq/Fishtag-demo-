#!/usr/bin/env python3
"""
Local preview server for the Fishtagged tag map.

The page loads vector tiles + JSON over http (not file://), so run this from
inside this folder, then open the printed URL.

    python3 serve.py
"""
import http.server, socketserver, functools, os

PORT = 8137
HERE = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".pbf": "application/x-protobuf"}
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()
    def log_message(self, *a):  # quiet
        pass

H = functools.partial(Handler, directory=HERE)
socketserver.TCPServer.allow_reuse_address = True
print("\n  Fishtagged running:  http://localhost:%d/index.html\n  (Ctrl-C to stop)\n" % PORT)
with socketserver.TCPServer(("127.0.0.1", PORT), H) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped.\n")
