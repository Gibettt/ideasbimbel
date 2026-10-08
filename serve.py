#!/usr/bin/env python3
import os
import sys
import mimetypes
import urllib.parse
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

BASE_DIR = Path(__file__).resolve().parent.parent if "www_crimsoneducation_org" in str(Path(__file__).resolve()) else Path(__file__).resolve().parent
SNAPSHOT_DIR = BASE_DIR / "crimson_snapshot"
MIRROR_DIR = BASE_DIR / "www_crimsoneducation_org"

class MultiRootHandler(SimpleHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.send_cors_headers()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()
    def do_GET(self):
        fpath = self.translate_path(self.path)
        if os.path.isfile(fpath) and fpath.endswith(".html"):
            try:
                with open(fpath, "rb") as f:
                    content = f.read()
                if b"http://localhost:9091/" in content:
                    content = content.replace(b"http://localhost:9091/", b"/")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception:
                pass
        super().do_GET()

    def translate_path(self, path):
        parsed = urllib.parse.urlparse(path)
        rel_path = urllib.parse.unquote(parsed.path).lstrip("/")

        # Handle root or directory
        if not rel_path or rel_path == "":
            rel_path = "index.html"
        elif rel_path == "id" or rel_path == "id/":
            rel_path = "id/index.html"

        # Check /_next/image?url=...
        if parsed.path.startswith("/_next/image") and parsed.query:
            qs = urllib.parse.parse_qs(parsed.query)
            orig_url = qs.get("url", [None])[0]
            if orig_url:
                inner = urllib.parse.urlparse(orig_url)
                inner_path = urllib.parse.unquote(inner.path).lstrip("/")
                for cand in [
                    SNAPSHOT_DIR / "_next_images" / inner_path,
                    SNAPSHOT_DIR / inner_path,
                    MIRROR_DIR / inner_path,
                ]:
                    if cand.is_file():
                        return str(cand)

        # Candidate paths to search
        candidates = []
        p_snapshot = SNAPSHOT_DIR / rel_path
        p_mirror = MIRROR_DIR / rel_path

        if p_snapshot.is_dir():
            candidates.append(p_snapshot / "index.html")
        candidates.append(p_snapshot)

        if p_mirror.is_dir():
            candidates.append(p_mirror / "index.html")
        candidates.append(p_mirror)

        # If missing extension or directory index
        if not rel_path.endswith(".html"):
            candidates.append(SNAPSHOT_DIR / (rel_path + ".html"))
            candidates.append(SNAPSHOT_DIR / rel_path / "index.html")
            candidates.append(MIRROR_DIR / (rel_path + ".html"))
            candidates.append(MIRROR_DIR / rel_path / "index.html")

        # Also check _next_images
        candidates.append(SNAPSHOT_DIR / "_next_images" / rel_path)

        for cand in candidates:
            if cand.is_file():
                return str(cand)

        # Default fallback to SNAPSHOT_DIR
        return str(SNAPSHOT_DIR / rel_path)

    def end_headers(self):
        self.send_cors_headers()
        super().end_headers()

    def log_message(self, fmt, *args):
        msg = fmt % args
        if " 404 " in msg or " 500 " in msg:
            sys.stderr.write(f"[WARN] {msg}\n")
        else:
            sys.stdout.write(f"[LOG] {msg}\n")
            sys.stdout.flush()

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9091
    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, MultiRootHandler)
    print(f"🚀 Threaded Server with No-Cache running on http://localhost:{port}/ (0.0.0.0:{port})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...", flush=True)
        httpd.server_close()

if __name__ == "__main__":
    main()
