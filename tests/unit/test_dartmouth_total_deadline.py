"""Real HTTP delays/timeouts must not defeat the free-model fallback budget."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from llmxive.backends import dartmouth
from llmxive.backends.base import ChatMessage, DeadlineExceededError
from llmxive.backends.router import chat_with_model_fallback

PRIMARY = "zai-org.glm-5.3"
PEER = "openai.gpt-oss-120b"


@pytest.fixture
def server(monkeypatch):
    import langchain_dartmouth.llms as sdk

    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            model = request["model"]
            calls.append(model)
            if model == PRIMARY:
                time.sleep(0.18)
                status = 503
                body = {"error": {"message": "Connection error.", "type": "server_error"}}
            else:
                status = 200
                body = {
                    "id": "local",
                    "object": "chat.completion",
                    "created": 0,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "healthy peer"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }
            raw = json.dumps(body).encode()
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    host = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=host.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", f"credential-free-local-test-{host.server_port}")
    monkeypatch.setattr(sdk, "CLOUD_BASE_URL", f"http://127.0.0.1:{host.server_port}/v1")
    monkeypatch.setattr(dartmouth, "_FREE_MODELS_CACHE", frozenset({PRIMARY, PEER}))
    try:
        yield calls
    finally:
        host.shutdown()
        host.server_close()
        thread.join(timeout=2)


def test_actual_sdk_read_timeout_falls_back_instead_of_becoming_permanent(server, monkeypatch):
    monkeypatch.setattr(dartmouth, "_deadline_for_model", lambda model: 2.0)
    monkeypatch.setattr(
        dartmouth, "_dartmouth_model_kwargs", lambda model: {"timeout": 0.05, "max_retries": 0}
    )
    backend = dartmouth.DartmouthBackend(max_retries=8, retry_base_delay_s=0)
    result = chat_with_model_fallback(
        backend,
        [ChatMessage(role="user", content="local HTTP probe")],
        model=PRIMARY,
        max_tokens=16,
    )
    assert result.model == PEER and result.text == "healthy peer"
    assert server == [PRIMARY, PEER]


def test_slow_transient_retries_share_one_total_model_deadline(server, monkeypatch):
    monkeypatch.setattr(dartmouth, "_deadline_for_model", lambda model: 0.30)
    monkeypatch.setattr(
        dartmouth, "_dartmouth_model_kwargs", lambda model: {"timeout": 2.0, "max_retries": 0}
    )
    backend = dartmouth.DartmouthBackend(max_retries=8, retry_base_delay_s=0)
    start = time.monotonic()
    with pytest.raises(DeadlineExceededError):
        backend.chat(
            [ChatMessage(role="user", content="local HTTP probe")], model=PRIMARY, max_tokens=16
        )
    assert time.monotonic() - start < 1.2
    assert len(server) <= 2
