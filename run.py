from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote
from getpass import getuser
from queue import Queue
from typing import Any
import subprocess
import mimetypes
import threading
import json
import os

config_path = os.path.join(os.environ["HOME"], ".config", "swing", "config.json")
if not os.path.exists(config_path):
    config_path = "config.json"

with open(config_path, "r") as content_file:
    raw_config = json.loads(content_file.read())

if not os.path.exists("dataset.json"):
    raise Exception("Missing core file dataset.json")

with open("dataset.json", "r") as content_file:
    dataset = json.loads(content_file.read())

config = raw_config.copy()

if "enabled" not in config:
    config["enabled"] = list(dataset.keys())

if "username" not in config:
    config["username"] = getuser()

commands: dict[str, Any] = {
    "config": config,
    "dataset": dataset,
}

command_queue: Queue[str] = Queue()
# Message, Error, Is This The End?
results: list[tuple[str, bool, bool]] = []

currently_launching: str | None = None

output = ""

cancelled = {}

def access_key(d: dict, k: str, fallback = None) -> Any:
    first, *last = k.split(".")

    if not first in d:
        return fallback

    return d[first] if len(last) == 0 else access_key(d[first], ".".join(last), fallback)

states: dict[str, bool] = {}

def run_queue():
    global command_queue
    global currently_launching
    global commands
    global output
    global states

    while True:
        if command_queue.not_empty:
            tag = command_queue.get()
            first, *last = tag.split(".")

            if first == "print":
                results.append((".".join(last), False, False))
                output += f"[print] {last}\n"
                break
            if first == "printend":
                results.append((".".join(last), False, True))
                output += f"[print] {last}\n"
                break
            if first == "addstate":
                states[".".join(last)] = True
                break

            print(tag, commands)

            commands_list: list[str] | str = access_key(
                commands,
                tag,
                [],
            )

            if isinstance(commands_list, str):
                commands_list = [commands_list]

            for i in range(len(commands_list)):
                command = commands_list[i]
                currently_launching = f"[{tag}] ({i}/{len(commands_list)}) {command}"

                output += currently_launching

                completed = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                output += f"{completed.stdout.decode("utf-8")}\n"

                results.append((currently_launching, completed.returncode != 0, False))

                if completed.returncode != 0:
                    break

            currently_launching = None


#     completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#     pending_error += f"$ {command}\n{completed.stdout.decode("utf-8")}\n"
#     if completed.returncode != 0:
#       error = pending_error
#       return


class LocalhostHTTPHandler(BaseHTTPRequestHandler):
    def redirect_to_home(self):
        self.send_response(301)
        self.send_header("Location", "/")
        self.end_headers()

    def do_GET(self):
        global cancelled

        if self.client_address[0] != "127.0.0.1":
            self.send_error(403, "Forbidden (only localhost allowed)")
            return

        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/status" or path == "/status/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            self.wfile.write(
                json.dumps([currently_launching, results]).encode(
                    "utf-8"
                )
            )
            return

        self.serve_static(path[1:])

    def do_POST(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        # if path.startswith("/cancel/"):
        #     to_cancel = path[8:]

        #     if to_cancel not in cancelled.keys():
        #         cancelled[to_cancel] = 0

        #     cancelled[to_cancel] += 1

        #     self.redirect_to_home()
        #     return

        if path.startswith("/start/"):
            self.handle_start(path[7:])  # Remove '/start/' prefix

    def serve_static(self, rel_path):
        if ".." in rel_path or rel_path.startswith("/"):
            self.send_error(403, "Forbidden")
            return

        if rel_path == "":
            rel_path = "index.html"

        if rel_path == "config.json":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            return self.wfile.write(json.dumps(config).encode())

        if rel_path == "dataset.json":
            rel_path = "../dataset.json"

        static_dir = "static"
        full_path = os.path.join(static_dir, rel_path)

        if not os.path.exists(full_path):
            self.send_error(404, "File not found")
            return

        mimetype = mimetypes.guess_type(f"file://{full_path}")[0]

        try:
            with open(full_path, "rb") as f:
                self.send_response(200)
                if mimetype is not None:
                    self.send_header("Content-type", mimetype)
                self.end_headers()

                self.wfile.write(f.read())
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def handle_start(self, param: str):
        global currently_launching

        if currently_launching is not None:
            self.send_error(423, "Cancel, then start anew")
            return

        if param not in dataset.keys():
            self.send_error(404, "No such DE")
            return

        if "enabled" in config.keys() and param not in config["enabled"]:
            self.send_error(403, "DE forbidden")
            return

        command_queue.put(f"dataset.{param}.commands")
        command_queue.put(f"config.additional.{param}")
        command_queue.put(f"config.additional.all")
        command_queue.put(f"dataset.{param}.launch")

        self.send_response(301)
        self.send_header("Location", f"/status.html?launching={param}")
        self.end_headers()


def run_server(port=8000):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, LocalhostHTTPHandler)

    command_queue.put(f"config.prepick")
    command_queue.put(f"addstate.prepick")
    command_queue.put(f"config.setup")

    background_thread = threading.Thread(target=run_queue)
    background_thread.daemon = True
    background_thread.start()

    print(f"Serving on http://127.0.0.1:{port}")
    os.system(f"firefox --new-window --kiosk http://127.0.0.1:{port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run_server(8000)
