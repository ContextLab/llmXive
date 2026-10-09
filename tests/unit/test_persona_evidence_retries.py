"""Transient source failures retry, permanent failures and mismatches still fail."""
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
import requests


@pytest.fixture
def verifier():
    path = Path(__file__).resolve().parents[2] / 'scripts/verify_persona_evidence.py'
    spec = importlib.util.spec_from_file_location('persona_evidence_retry_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def source():
    replies = []
    seen = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            status, body = replies.pop(0)
            self.send_response(status)
            self.end_headers()
            self.wfile.write(body.encode())
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}/citation', replies, seen
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.mark.parametrize('status', [429, 500, 502, 503, 504])
def test_transient_http_failure_recovers_using_actual_response(verifier, source, status):
    url, replies, seen = source
    replies.extend([(status, 'temporary'), (200, 'Evidence about prospect theory')])
    assert verifier._verify_url(url, ['prospect'])[0]
    assert len(seen) == 2


@pytest.mark.parametrize('responses,expected_calls', [
    ([(404, 'missing')], 1),
    ([(200, 'unrelated body')], 1),
    ([(503, 'down')] * 3, 3),
])
def test_failure_never_turns_into_acceptance(verifier, source, responses, expected_calls):
    url, replies, seen = source
    replies.extend(responses)
    assert not verifier._verify_url(url, ['prospect'])[0]
    assert len(seen) == expected_calls


def test_read_timeout_retries_then_fetches_real_source(verifier, source, monkeypatch):
    url, replies, seen = source
    replies.append((200, 'Evidence about prospect theory'))
    real_get = requests.get
    attempts = []
    def timeout_once(*args, **kwargs):
        attempts.append(1)
        if len(attempts) == 1:
            raise requests.ReadTimeout('temporary source timeout')
        return real_get(*args, **kwargs)
    monkeypatch.setattr(verifier.requests, 'get', timeout_once)
    assert verifier._verify_url(url, ['prospect'])[0]
    assert len(attempts) == 2 and len(seen) == 1
