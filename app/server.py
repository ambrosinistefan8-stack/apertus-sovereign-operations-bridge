from __future__ import annotations
import json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .apertus_client import MockApertusClient, OpenAICompatibleApertusClient
from .fixtures import scenario_documents
from .service import run_workflow

ROOT=Path(__file__).resolve().parent.parent
STATIC=ROOT/"static"

def _client():
    return OpenAICompatibleApertusClient() if os.environ.get("APERTUS_MODE","mock").lower()=="live" else MockApertusClient()

class Handler(BaseHTTPRequestHandler):
    def _json(self,status,payload):
        body=json.dumps(payload,ensure_ascii=False,indent=2).encode()
        self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        if self.path=="/":
            body=(STATIC/"index.html").read_bytes()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body); return
        if self.path=="/health": self._json(200,{"status":"ok","mode":os.environ.get("APERTUS_MODE","mock")}); return
        self._json(404,{"error":"not_found"})

    def do_POST(self):
        if self.path!="/api/run": self._json(404,{"error":"not_found"}); return
        try:
            length=int(self.headers.get("Content-Length","0"))
            payload=json.loads(self.rfile.read(length).decode())
            result=run_workflow(_client(),payload.get("task","Prepare the correct customer response."),scenario_documents(payload.get("scenario","normal")),["product","price_chf","delivery_days"])
            self._json(200,result)
        except Exception as exc:
            self._json(500,{"error":type(exc).__name__,"message":str(exc)})

def main():
    host=os.environ.get("HOST","127.0.0.1"); port=int(os.environ.get("PORT","8080"))
    print(f"Apertus Sovereign Operations Bridge running on http://{host}:{port}")
    print(f"Mode: {os.environ.get('APERTUS_MODE','mock')}")
    ThreadingHTTPServer((host,port),Handler).serve_forever()

if __name__=="__main__": main()
