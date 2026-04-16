import asyncio
import os
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK


HOST = "0.0.0.0"
HTTP_PORT = 5000
WS_PORT = 5001
MAX_WAV_BYTES = 12_000_000  # ~12 MB safety limit


def play_wav_bytes(audio_data: bytes) -> tuple[bool, str]:
    if not audio_data:
        return False, "empty audio payload"
    if len(audio_data) > MAX_WAV_BYTES:
        return False, f"payload too large: {len(audio_data)} bytes"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_data)
            tmp_path = f.name

        p = subprocess.run(
            ["aplay", "-q", tmp_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if p.returncode == 0:
                        return True, "played"

        err = (p.stderr or "").strip()
        if not err:
            err = "aplay failed"
        return False, err

    except Exception as e:
        return False, str(e)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


class AudioHttpHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return  # silence default logs

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"audio server running")
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/play":
            self.send_response(404)
            self.end_headers()
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"error: missing body")
                return
            if content_length > MAX_WAV_BYTES:
                self.send_response(413)
                self.end_headers()
                self.wfile.write(b"error: payload too large")
                return

            audio_data = self.rfile.read(content_length)
            ok, msg = play_wav_bytes(audio_data)

            if ok:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"played")
            else:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"error: {msg}".encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"error: {e}".encode("utf-8"))


async def ws_audio_handler(websocket, *args):
    print("WS client connected")
    try:
        async for message in websocket:
            if not isinstance(message, (bytes, bytearray)):
                await websocket.send("error: send binary wav bytes")
                continue

            print(f"received {len(message)} bytes")

            ok, msg = play_wav_bytes(bytes(message))
            if ok:
                await websocket.send("played")
            else:
                await websocket.send(f"error: {msg}")

    except ConnectionClosedOK:
        print("WS client disconnected (normal)")
    except ConnectionClosedError as e:
        print(f"WS client disconnected (error): {e}")
    except Exception as e:
        print(f"WS handler error: {e}")


def run_http_server():
    server = ThreadingHTTPServer((HOST, HTTP_PORT), AudioHttpHandler)
    print(f"HTTP audio server running on {HOST}:{HTTP_PORT}")
    server.serve_forever()


async def run_ws_server():
    print(f"WS audio server running on {HOST}:{WS_PORT}")
    async with websockets.serve(
        ws_audio_handler,
        HOST,
        WS_PORT,
        max_size=MAX_WAV_BYTES,
    ):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    asyncio.run(run_ws_server())