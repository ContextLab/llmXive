"""Later implementation edits do not change the role of research runbooks."""
from dataclasses import replace

import pytest

from llmxive.claims import service
from tests.unit.test_planning_skip import _Backend, _lowlevel_claim, DOC


@pytest.mark.parametrize('name', ['spec.md', 'plan.md', 'research.md', 'data-model.md', 'quickstart.md'])
def test_implementer_planning_documents_never_resolve_external_facts(tmp_path, monkeypatch, name):
    artifact = f'projects/PROJ-x/specs/001-feature/{name}'
    stages = []
    def extract(*a, **kw):
        stages.append(kw.get('stage_label'))
        return [replace(_lowlevel_claim(), artifact_path=artifact)]
    monkeypatch.setattr(service, 'extract_claims', extract)
    def forbidden(*a, **k):
        pytest.fail('runbook was sent to external factual resolution')
    monkeypatch.setattr(service, 'resolve', forbidden)
    text, claims, gate = service.process_document(DOC, artifact_path=artifact,
        project_id='PROJ-x', backend=_Backend(), model=None, repo_root=tmp_path,
        stage_label='implement')
    assert stages == ['plan']
    assert not gate.blocked and claims == []
    assert '49' not in text  # unsupported empirical count is deferred, not certified
    assert 'Rolfsen 1976' in text
    assert 'method enumerates knots' in text


@pytest.mark.parametrize('artifact', [
    'projects/PROJ-x/data/results/quickstart.md',
    'projects/PROJ-x/specs/001-feature/RESULTS.md',
    'projects/PROJ-x/paper/specs/001-feature/spec.md',
    'projects/PROJ-other/specs/001-feature/plan.md',
    'projects/PROJ-x/specs/../plan.md',
    '/projects/PROJ-x/specs/001-feature/plan.md',
])
def test_results_papers_and_other_project_paths_keep_full_verification(tmp_path, monkeypatch, artifact):
    from llmxive.claims.stage import is_research_planning_artifact
    assert not is_research_planning_artifact(artifact, 'PROJ-x')
    monkeypatch.setattr(service, 'extract_claims', lambda *a, **kw: [
        replace(_lowlevel_claim(), artifact_path=artifact)])
    def verify(*a, **kw):
        raise RuntimeError('full verification required')
    monkeypatch.setattr(service, 'resolve', verify)
    with pytest.raises(RuntimeError, match='full verification required'):
        service.process_document(DOC, artifact_path=artifact, project_id='PROJ-x',
            backend=_Backend(), model=None, repo_root=tmp_path, stage_label='implement')
