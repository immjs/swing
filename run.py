from http.server import HTTPServer, BaseHTTPRequestHandler
from posixpath import relpath
from urllib.parse import urlparse, unquote
import os
import mimetypes
import subprocess

class LocalhostHTTPHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    if self.client_address[0] != '127.0.0.1':
      self.send_error(403, "Forbidden (only localhost allowed)")
      return

    parsed = urlparse(self.path)
    path = unquote(parsed.path)

    if path.startswith('/start/'):
      self.handle_start(path[7:])  # Remove '/start/' prefix
    else:
      self.serve_static(path[1:])

  def serve_static(self, rel_path):
    if '..' in rel_path or rel_path.startswith('/'):
      self.send_error(403, "Forbidden")
      return

    if rel_path == '':
      rel_path = 'index.html'

    if rel_path == 'allowed_de.json':
      rel_path = '../allowed_de.json'

    static_dir = 'static'
    full_path = os.path.join(static_dir, rel_path)

    if not os.path.exists(full_path):
      self.send_error(404, "File not found")
      return

    mimetype = mimetypes.guess_type(f"file://{full_path}")[0]

    try:
      with open(full_path, 'rb') as f:
        self.send_response(200)
        if mimetype is not None:
          self.send_header('Content-type', mimetype)
        self.end_headers()

        self.wfile.write(f.read())
    except Exception as e:
      self.send_error(500, f"Server error: {str(e)}")

  def handle_start(self, param):
    self.send_response(200)
    self.send_header('Content-type', 'text/plain')
    self.end_headers()
    self.wfile.write(f"You accessed /start/{param}".encode())

def run_server(port=8000):
  server_address = ('127.0.0.1', port)
  httpd = HTTPServer(server_address, LocalhostHTTPHandler)
  print(f"Serving on http://127.0.0.1:{port}")
  os.system("firefox --new-window --kiosk http://127.0.0.1:8000")
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    print("\nServer shutting down...")
  finally:
    httpd.server_close()

if __name__ == '__main__':
  run_server(8000)
