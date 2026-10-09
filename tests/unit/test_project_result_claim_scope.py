"""Project outcomes require local receipts, never external lookup/fill."""
import pytest
import yaml
from llmxive.claims.extract import _parse_extraction_reply
from llmxive.claims.models import ClaimKind, ClaimStatus
from llmxive.claims.resolve import resolve


@pytest.mark.parametrize('text', [
    'The run reports all totients match validation.',
    'No conditional TV reversals were detected.',
    'Our model causes a 10 percent reduction in error.',
    'Our benchmark was faster than the baseline.',
])
def test_project_result_scope_overrides_wording_and_cannot_be_filled(tmp_path, monkeypatch, text):
    monkeypatch.setenv('LLMXIVE_RECEIPT_KEY', 'test-receipt-key')
    monkeypatch.setenv('LLMXIVE_CLAIM_FILL', '1')
    claim = _parse_extraction_reply(yaml.safe_dump({'claims': [{
        'claim_text': text, 'canonical': text, 'evidence_scope': 'project_result'}]}),
        'projects/PROJ-1/data/results/RESULTS.md')[0]
    assert claim.kind == ClaimKind.RESULT and claim.source_type == 'result'
    class ForbiddenBackend:
        def chat(self, *args, **kwargs):
            pytest.fail('project outcome reached external/model resolver')
    verdict = resolve(claim, backend=ForbiddenBackend(), model='test', repo_root=tmp_path)
    assert verdict.status == ClaimStatus.NOT_ENOUGH_INFO
    assert verdict.resolver == 'resolve_result'


def test_quote_fragile_reply_preserves_project_result_scope():
    raw = '''claims:
  - claim_text: "The run reports "all totients match"."
    canonical: "all totients match validation"
    evidence_scope: "project_result" # current experiment
'''
    claim = _parse_extraction_reply(raw, 'projects/PROJ-1/results.md')[0]
    assert claim.kind == ClaimKind.RESULT


def test_external_fact_keeps_external_resolution():
    claim = _parse_extraction_reply(yaml.safe_dump({'claims': [{
        'claim_text': 'The published dataset contains 9988 prime knots.',
        'canonical': '9988 prime knots', 'evidence_scope': 'external'}]}),
        'projects/PROJ-1/results.md')[0]
    assert claim.kind == ClaimKind.NUMERIC and claim.source_type == 'external'


def test_explicit_other_study_result_is_not_our_execution_result():
    claim = _parse_extraction_reply(yaml.safe_dump({'claims': [{
        'claim_text': 'The cited study reports that accuracy was 91 percent.',
        'evidence_scope': 'external'}]}), 'projects/PROJ-1/results.md')[0]
    assert claim.kind == ClaimKind.NUMERIC and claim.source_type == 'external'
