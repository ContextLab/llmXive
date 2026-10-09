"""Prose must be grounded in authenticated bytes, with fresh cache evidence."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from llmxive.claims.models import ClaimKind, ClaimStatus
from llmxive.claims.resolve import resolve_result
from llmxive.claims.service import resolve_registered_claims
from llmxive.execution.stage import _mint_artifact_receipts
from tests.unit.test_planning_skip import _Backend, _lowlevel_claim

DATA = '{"N":10000,"p":5,"tv_unconditional":0.1452}'
TEXT = 'For N=10000 and p=5, our unconditional TV was 0.1452.'


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    monkeypatch.setenv('LLMXIVE_RECEIPT_KEY', 'ephemeral-test-result-prose-key')
    project = tmp_path/'projects/PROJ-results'
    file = project/'data/summary.json'
    file.parent.mkdir(parents=True)
    file.write_text(DATA)
    _mint_artifact_receipts(project, SimpleNamespace(artifacts_produced=['data/summary.json']), tmp_path)
    claim = replace(_lowlevel_claim(), claim_id='c_resultprose', kind=ClaimKind.RESULT,
        raw_text=TEXT, canonical=TEXT, source_type='result',
        artifact_path='projects/PROJ-results/docs/research.md')
    return tmp_path, project, file, claim


def backend(status='grounded', quote=DATA):
    import yaml
    return _Backend(reply=yaml.safe_dump({'status':status, 'evidence':quote, 'note':'fixture verdict'}))


def test_grounded_prose_preserved_and_cache_invalidated(fixture):
    root, project, file, claim = fixture
    model = backend()
    def run():
        return resolve_registered_claims([claim], project_id=project.name, backend=model,
                                         model=None, repo_root=root)[0]
    first = run()
    assert first.status == ClaimStatus.VERIFIED
    assert first.resolved_value == TEXT
    assert first.evidence['result_artifacts'][0]['path'] == 'data/summary.json'
    assert run().status == ClaimStatus.VERIFIED
    assert len(model.calls) == 1
    file.write_text(DATA.replace('0.1452', '0.99'))
    assert run().status == ClaimStatus.NOT_ENOUGH_INFO
    assert len(model.calls) == 1  # stale bytes never sent to entailment


@pytest.mark.parametrize('change', ['unsigned', 'tampered', 'deleted', 'symlink'])
def test_untrusted_artifact_never_reaches_model(fixture, change):
    root, project, file, claim = fixture
    if change == 'unsigned':
        for path in (root/'state/results').rglob('*.yaml'): path.unlink()
    elif change == 'tampered':
        file.write_text('arbitrary replacement')
    elif change == 'deleted':
        file.unlink()
    else:
        copy=root/'outside.json'; copy.write_text(DATA);file.unlink();file.symlink_to(copy)
    model = backend()
    result = resolve_result(claim,backend=model,model=None,repo_root=root)
    assert result.status == ClaimStatus.NOT_ENOUGH_INFO
    assert not model.calls


def test_fabricated_model_quote_cannot_ground_result(fixture):
    root, _, _, claim = fixture
    result=resolve_result(claim, backend=backend(quote='not actually present'),model=None,repo_root=root)
    assert result.status==ClaimStatus.NOT_ENOUGH_INFO


def test_missing_reported_number_rejects_false_positive_model(fixture):
    root, _, _, claim = fixture
    claim=replace(claim,raw_text=TEXT.replace('0.1452','0.018'))
    result=resolve_result(claim,backend=backend(),model=None,repo_root=root)
    assert result.status==ClaimStatus.NOT_ENOUGH_INFO


def test_contradicted_result_is_refuted_without_filling(fixture):
    root, _, _, claim = fixture
    claim=replace(claim,raw_text=TEXT.replace('0.1452','0.018'))
    result=resolve_result(claim,backend=backend('contradicted'),model=None,repo_root=root)
    assert result.status==ClaimStatus.REFUTED
    assert result.value is None


def test_change_during_entailment_cannot_be_accepted(fixture):
    root, _, file, claim = fixture
    model=backend();original=model.chat
    def chat(*args,**kwargs):
        file.write_text(DATA.replace('0.1452','0.9'))
        return original(*args,**kwargs)
    model.chat=chat
    result=resolve_result(claim,backend=model,model=None,repo_root=root)
    assert result.status==ClaimStatus.NOT_ENOUGH_INFO


def test_prose_rendering_does_not_replace_a_number_with_a_sentence(fixture):
    from llmxive.claims.pointer import _render_verified
    root, project, _, claim = fixture
    resolved=resolve_registered_claims([claim],project_id=project.name,
        backend=backend(),model=None,repo_root=root)[0]
    assert _render_verified(resolved)==TEXT


def test_new_claim_cannot_inherit_prose_as_a_scalar_correction(fixture):
    root, project, _, claim = fixture
    model=backend()
    resolve_registered_claims([claim],project_id=project.name,backend=model,model=None,repo_root=root)
    rephrased=replace(claim,claim_id='c_newmention',context='different paragraph')
    result=resolve_registered_claims([rephrased],project_id=project.name,
        backend=model,model=None,repo_root=root)[0]
    assert result.status==ClaimStatus.VERIFIED
    assert len(model.calls)==2


def test_large_authenticated_file_is_not_read_into_prompt(fixture):
    root, project, file, claim=fixture
    file.write_text(DATA*1000)
    _mint_artifact_receipts(project,SimpleNamespace(artifacts_produced=['data/summary.json']),root)
    model=backend()
    result=resolve_result(claim,backend=model,model=None,repo_root=root)
    assert result.status==ClaimStatus.NOT_ENOUGH_INFO
    assert not model.calls
