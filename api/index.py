from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/health" or self.path == "/api/health":
            data = {
                "ok": True,
                "message": "Python funcionando en Vercel",
                "path": self.path
            }

            raw = json.dumps(data).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not found")