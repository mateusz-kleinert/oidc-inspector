"""Ephemeral local HTTP server that captures the OIDC authorization code redirect."""

import queue
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

_SUCCESS_HTML = (
    "<!DOCTYPE html>"
    '<html lang="en"><head><meta charset="utf-8">'
    "<title>OIDC Inspector - Authentication Successful</title>"
    "<style>"
    "body{font-family:system-ui,sans-serif;text-align:center;padding:4em;background:#f0f4f8}"
    ".card{background:#fff;border-radius:8px;padding:2em 3em;display:inline-block;"
    "box-shadow:0 2px 8px rgba(0,0,0,.12)}"
    "h1{color:#1a7f4b}"
    "</style></head><body>"
    '<div class="card">'
    "<h1>&#10003; Authentication Successful</h1>"
    "<p>You can close this tab and return to the terminal.</p>"
    "</div></body></html>"
).encode()

_ERROR_HTML = (
    "<!DOCTYPE html>"
    '<html lang="en"><head><meta charset="utf-8">'
    "<title>OIDC Inspector - Authentication Failed</title>"
    "<style>"
    "body{font-family:system-ui,sans-serif;text-align:center;padding:4em;background:#f0f4f8}"
    ".card{background:#fff;border-radius:8px;padding:2em 3em;display:inline-block;"
    "box-shadow:0 2px 8px rgba(0,0,0,.12)}"
    "h1{color:#c0392b}"
    "</style></head><body>"
    '<div class="card">'
    "<h1>&#10007; Authentication Failed</h1>"
    "<p>An error was returned by the provider. Check the terminal for details.</p>"
    "</div></body></html>"
).encode()


def _make_handler(result_queue: "queue.Queue[dict[str, Any]]") -> type:
    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return

            raw = parse_qs(parsed.query, keep_blank_values=True)
            params = {k: v[0] if len(v) == 1 else v for k, v in raw.items()}
            result_queue.put(params)

            body = _ERROR_HTML if "error" in params else _SUCCESS_HTML
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: object) -> None:  # silence access log
            pass

    return CallbackHandler


def wait_for_callback(port: int, timeout: int = 120) -> dict[str, Any]:
    """Start a local server on *port*, block until /callback is hit, then shut down.

    Returns the query-string parameters from the redirect as a flat dict.
    Raises ``TimeoutError`` if no request arrives within *timeout* seconds.
    """
    result_queue: queue.Queue[dict[str, Any]] = queue.Queue()
    server = HTTPServer(("127.0.0.1", port), _make_handler(result_queue))

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        return result_queue.get(timeout=timeout)
    except queue.Empty:
        raise TimeoutError(
            f"No callback received on port {port} within {timeout} seconds. "
            "Did you complete the browser login?"
        )
    finally:
        server.shutdown()
