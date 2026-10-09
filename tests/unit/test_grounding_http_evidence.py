"""Grounding needs a successful source response and a real source quotation."""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest

from llmxive.claims.models import ClaimStatus
from llmxive.grounding.entailment import assess
from llmxive.grounding.full_text import _fetch_url_text
from llmxive.state.claims import _dict_to_claim


@pytest.mark.parametrize('status', [200, 403, 404, 500])
def test_error_page_body_is_not_evidence(status):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(status)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<p>The reported effect is 42 percent.</p>')
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        text, _ = _fetch_url_text(f'http://127.0.0.1:{server.server_port}/article', timeout=2)
        assert bool(text) == (status == 200)
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


@pytest.mark.parametrize('quote,expected', [
    ('The reported effect is 42 percent.', 'grounded'),
    ('The reported effect is 99 percent.', 'not_found'),
    ('', 'not_found'),
])
def test_invented_supporting_quote_is_rejected(tmp_path, monkeypatch, quote, expected):
    import json

    from llmxive.grounding import entailment
    doc = SimpleNamespace(full_text='The reported effect is 42 percent.', abstract=None)
    monkeypatch.setattr(entailment, 'load_prompt', lambda *a, **k: 'Only quote retrieved passages.')
    monkeypatch.setattr(entailment, 'reasoning_chat', lambda *a, **k: SimpleNamespace(
        text=json.dumps({'status': 'grounded', 'evidence': quote})))
    assert assess('The reported effect is 42 percent.', doc, backend=None, model='test',
                  repo_root=tmp_path).status == expected


def test_legacy_grounding_receipt_requires_new_validation():
    record = dict(claim_id='c_12345678', kind='entity_fact', raw_text='claim', canonical='claim',
                  context='', artifact_path='results.md', source_type='external', status='verified',
                  evidence={'entailment_status': 'grounded', 'source_url': 'https://example.org/x'})
    assert _dict_to_claim(record).status == ClaimStatus.PENDING
    record['evidence']['source_validation_version'] = 2
    assert _dict_to_claim(record).status == ClaimStatus.VERIFIED


def test_carried_legacy_pointer_is_revalidated_before_render(tmp_path, monkeypatch):
    from llmxive.claims import service
    from llmxive.claims.models import Claim, ClaimKind, Verdict
    from llmxive.state import claims
    claim = Claim(claim_id='c_12345678', kind=ClaimKind.ENTITY_FACT, raw_text='Effect is 42 percent.',
                  canonical='Effect is 42 percent.', context='', artifact_path='results.md',
                  source_type='external', status=ClaimStatus.VERIFIED, resolved_value='42 percent',
                  evidence={'entailment_status': 'grounded', 'source_url': 'https://example.org/error'},
                  resolver='resolve_entity_fact', attempts=1, updated_at='2026-10-09T00:00:00Z')
    claims.save('PROJ-1', [claim], repo_root=tmp_path)
    monkeypatch.setattr(service, 'extract_claims', lambda *a, **k: [])
    seen = []
    def resolve(current, **kwargs):
        seen.append(current.claim_id)
        return Verdict(status=ClaimStatus.NOT_ENOUGH_INFO, value=None,
                       evidence={'reason': 'HTTP 404'}, resolver='resolve_entity_fact')
    monkeypatch.setattr(service, 'resolve', resolve)
    _, _, gate = service.process_document('{{claim:c_12345678}}', artifact_path='results.md',
        project_id='PROJ-1', backend=None, model=None, repo_root=tmp_path)
    assert seen == ['c_12345678']
    assert gate.blocked
    assert claims.get('PROJ-1', claim.claim_id, repo_root=tmp_path).status == ClaimStatus.NOT_ENOUGH_INFO
