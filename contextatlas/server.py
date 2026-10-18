"""Zero-dependency local demo server. Bind to loopback by default."""
from __future__ import annotations
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .engine import analyze
ROOT=Path(__file__).resolve().parent.parent
STATIC={"/":"web/index.html","/styles.css":"web/styles.css","/app.js":"web/app.js"}
TYPES={".html":"text/html; charset=utf-8",".css":"text/css; charset=utf-8",".js":"text/javascript; charset=utf-8"}
class Handler(BaseHTTPRequestHandler):
    def _respond(self,status,data,ctype="application/json; charset=utf-8"):
        self.send_response(status);self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(len(data)));self.send_header("X-Content-Type-Options","nosniff");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(data)
    def do_GET(self):
        path=self.path.split("?",1)[0]
        if path=="/api/health":return self._respond(200,b'{"status":"ok","mode":"local"}')
        if path=="/api/demo":return self._respond(200,(ROOT/"datasets/demo.json").read_bytes())
        if path not in STATIC:return self._respond(404,b'{"error":"Not found"}')
        file=ROOT/STATIC[path]
        return self._respond(200,file.read_bytes(),TYPES[file.suffix])
    def do_POST(self):
        if self.path!="/api/analyze":return self._respond(404,b'{"error":"Not found"}')
        try:
            length=int(self.headers.get("Content-Length","0"))
            if length<1 or length>250000:return self._respond(413,b'{"error":"Payload must be 1..250000 bytes"}')
            body=json.loads(self.rfile.read(length));data=analyze(body.get("query",""),body.get("chunks",[]),body.get("budget",120),body.get("diversity",0.55))
            self._respond(200,json.dumps(data).encode())
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
            self._respond(400,json.dumps({"error":str(exc)}).encode())
    def log_message(self,fmt,*args):pass

def serve(host="127.0.0.1",port=8765):
    server=ThreadingHTTPServer((host,port),Handler)
    print(f"ContextAtlas running at http://{host}:{port} (Ctrl+C to stop)")
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
