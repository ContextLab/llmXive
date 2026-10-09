"""Signed result receipts must match the current project artifact bytes."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from llmxive.claims import service
from llmxive.claims.models import ClaimKind, ClaimStatus
from llmxive.execution.stage import _mint_artifact_receipts
from llmxive.results.harness import result_backed
from llmxive.state import claims as claim_store
from tests.unit.test_planning_skip import _lowlevel_claim


@pytest.fixture
def artifact(tmp_path, monkeypatch):
    monkeypatch.setenv('LLMXIVE_RECEIPT_KEY', 'ephemeral-test-only-receipt-key')
    project = tmp_path/'projects/PROJ-receipt'
    file = project/'data/results/summary.csv'
    file.parent.mkdir(parents=True)
    file.write_text('N,count\n10,10\n')
    _mint_artifact_receipts(project, SimpleNamespace(artifacts_produced=['data/results/summary.csv']), tmp_path)
    return tmp_path, project, file


def backed(artifact):
    root, project, file = artifact
    return result_backed(str(file.relative_to(project)), project.name, repo_root=root)


@pytest.mark.parametrize('change', ['rewrite', 'delete', 'symlink'])
def test_signed_receipt_rejected_after_artifact_changes(artifact, change):
    root, project, file = artifact
    assert backed(artifact) is not None
    if change == 'rewrite':
        file.write_text('N,count\n10,999\n')
    elif change == 'delete':
        file.unlink()
    else:
        outside=root/'outside.csv'; outside.write_bytes(file.read_bytes())
        file.unlink(); file.symlink_to(outside)
    assert backed(artifact) is None


def test_result_cache_invalidates_and_refreshes_after_new_execution(artifact):
    root, project, file = artifact
    rel=str(file.relative_to(project))
    claim=replace(_lowlevel_claim(), claim_id='c_artifact', kind=ClaimKind.RESULT,
        raw_text=rel, canonical=rel, artifact_path=f'projects/{project.name}/data/results/RESULTS.md',
        source_type='result')
    def resolve(item):
        return service.resolve_registered_claims([item],project_id=project.name,
            backend=None,model=None,repo_root=root)[0]
    first=resolve(claim)
    assert first.status==ClaimStatus.VERIFIED
    file.write_text('N,count\n20,20\n')
    stale=resolve(claim)
    assert stale.status==ClaimStatus.NOT_ENOUGH_INFO
    _mint_artifact_receipts(project,SimpleNamespace(artifacts_produced=[rel]),root)
    refreshed=resolve(claim)
    assert refreshed.status==ClaimStatus.VERIFIED
    assert refreshed.source_hash!=first.source_hash


def test_legacy_hashless_verified_result_cannot_survive_deleted_artifact(artifact):
    root,project,file=artifact
    rel=str(file.relative_to(project))
    claim=replace(_lowlevel_claim(),claim_id='c_legacy',kind=ClaimKind.RESULT,
        raw_text=rel,canonical=rel,resolved_value=rel,source_hash=None,status=ClaimStatus.VERIFIED,
        artifact_path=f'projects/{project.name}/data/results/RESULTS.md',source_type='result')
    claim_store.upsert(project.name,claim,repo_root=root)
    file.unlink()
    result=service.resolve_registered_claims([claim],project_id=project.name,
        backend=None,model=None,repo_root=root)[0]
    assert result.status==ClaimStatus.NOT_ENOUGH_INFO


def test_receipt_key_not_exposed_to_research_child(tmp_path, monkeypatch):
    import os,subprocess,sys
    from llmxive.sandbox import analysis_environment
    monkeypatch.setenv('LLMXIVE_RECEIPT_KEY','ephemeral-test-only-receipt-key')
    result=subprocess.run([sys.executable,'-c',
        "import os; assert 'LLMXIVE_RECEIPT_KEY' not in os.environ; print('isolated')"],
        env=analysis_environment(tmp_path),capture_output=True,text=True,check=True)
    assert result.stdout.strip()=='isolated'


def test_rephrased_result_cannot_inherit_a_stale_verified_twin(artifact):
    root,project,file=artifact
    rel=str(file.relative_to(project))
    claim=replace(_lowlevel_claim(),claim_id='c_original',kind=ClaimKind.RESULT,
        raw_text=rel,canonical=rel,artifact_path=f'projects/{project.name}/data/results/RESULTS.md',
        source_type='result')
    first=service.resolve_registered_claims([claim],project_id=project.name,
        backend=None,model=None,repo_root=root)[0]
    assert first.status==ClaimStatus.VERIFIED
    file.write_text('different results\n')
    rephrased=replace(claim,claim_id='c_rephrased',context='another paragraph')
    result=service.resolve_registered_claims([rephrased],project_id=project.name,
        backend=None,model=None,repo_root=root)[0]
    assert result.status==ClaimStatus.NOT_ENOUGH_INFO
