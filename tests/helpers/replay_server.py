"""A real local HTTP server that replays recorded responses (no mocks of the client).

``ReplayServer(routes)`` binds ``127.0.0.1:0``. ``routes`` maps ``(method, path)`` to
either a list of ``(status, json_body)`` served in order (the last one repeats) or a
callable taking the recorded request dict and returning ``(status, json_body)``.
Every request is recorded in ``.requests`` with ``method``, ``path``, ``query``
(first value per key), ``headers`` (lower-cased names) and ``json`` (or ``None``).
A body given as ``bytes`` is sent verbatim (for non-JSON replies). A reply may carry a
third element, a dict of extra response headers (e.g. ``{"Location": ...}``).
A reply that is the :data:`DROP` sentinel closes the connection without any response
(the client sees the server disconnect mid-request).
An unrouted request is answered 404 and still recorded.

Requests are served concurrently, like a real server: a callable route runs OUTSIDE
the server's lock, so a handler that blocks (e.g. on a ``threading.Event`` the test
releases) never holds up another request. Recording and list-route cursors stay
serialised. A test whose handler blocks must release it before the ``with`` block
ends: closing the server waits for every handler thread.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit


class _Drop:
    def __repr__(self) -> str:
        return "DROP"


#: Reply sentinel: close the connection without sending a response.
DROP = _Drop()

Reply = tuple[int, dict | bytes] | tuple[int, dict | bytes, dict[str, str]] | _Drop
Route = list[Reply] | Callable[[dict], Reply]


class ReplayServer:
    def __init__(self, routes: dict[tuple[str, str], Route]) -> None:
        self._routes = routes
        self._cursor: dict[tuple[str, str], int] = {}
        self._lock = threading.Lock()
        self.requests: list[dict] = []
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        assert self._server is not None, "use ReplayServer as a context manager"
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def _respond(self, method: str, handler: BaseHTTPRequestHandler) -> None:
        parts = urlsplit(handler.path)
        length = int(handler.headers.get("Content-Length") or 0)
        raw = handler.rfile.read(length) if length else b""
        record = {
            "method": method,
            "path": parts.path,
            "query": {k: v[0] for k, v in parse_qs(parts.query).items()},
            "headers": {k.lower(): v for k, v in handler.headers.items()},
            "json": json.loads(raw) if raw else None,
        }
        key = (method, parts.path)
        with self._lock:
            self.requests.append(record)
            route = self._routes.get(key)
            reply: Reply | None
            if route is None:
                reply = (404, {"error": "no route"})
            elif callable(route):
                reply = None  # run below, outside the lock
            else:
                i = self._cursor.get(key, 0)
                reply = route[min(i, len(route) - 1)]
                self._cursor[key] = i + 1
        if reply is None:
            reply = route(record)  # type: ignore[misc,operator]
        if isinstance(reply, _Drop):
            handler.close_connection = True  # no status line, no body: a dropped connection
            return
        status, body = reply[0], reply[1]
        extra = reply[2] if len(reply) > 2 else {}
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        handler.send_response(status)
        for name, value in extra.items():
            handler.send_header(name, value)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)

    def __enter__(self) -> ReplayServer:
        outer = self

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                outer._respond("GET", self)

            def do_POST(self) -> None:
                outer._respond("POST", self)

            def log_message(self, *args: object) -> None:
                pass

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        assert self._server is not None and self._thread is not None
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
