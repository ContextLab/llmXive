"""The real SDK must not multiply retries behind the outer deadline/router."""
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


@pytest.mark.parametrize('failure', ['unavailable', 'read_timeout'])
def test_real_sdk_does_not_repeat_failed_http_requests(monkeypatch, failure):
    import langchain_dartmouth.llms as sdk
    from langchain_core.messages import HumanMessage
    from llmxive.backends import dartmouth
    calls = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            calls.append(self.path)
            self.rfile.read(int(self.headers.get('Content-Length', '0')))
            if failure == 'read_timeout':
                time.sleep(0.25)
            body = b'{"error":{"message":"temporarily unavailable","type":"server_error"}}'
            try:
                self.send_response(503)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv('DARTMOUTH_CHAT_API_KEY','credential-free-local-sdk-test')
    monkeypatch.setattr(sdk,'CLOUD_BASE_URL',f'http://127.0.0.1:{server.server_port}/v1')
    monkeypatch.setattr(dartmouth,'_DEFAULT_REASONING_DEADLINE_S',0.08 if failure == 'read_timeout' else 2.0)
    try:
        client = dartmouth.DartmouthBackend(max_retries=0)._client('zai-org.glm-5.3')
        with pytest.raises(Exception):
            client.invoke([HumanMessage(content='local retry boundary')], max_tokens=8)
        assert calls == ['/v1/chat/completions']
        assert client.root_client.max_retries == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
