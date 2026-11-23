"""The production post-write citation pass must preserve recovered source bytes."""
from types import SimpleNamespace

import pytest

from llmxive.speckit.implement_cmd import ImplementerAgent
from llmxive.speckit.slash_command import _validate_artifact_citations


@pytest.mark.parametrize('suffix', ['.md', '.markdown', '.tex'])
def test_writer_then_citation_pass_preserves_archive_but_cleans_new_output(tmp_path, monkeypatch, suffix):
    project = tmp_path / 'projects/PROJ-999-archive-preservation'
    (project / 'code').mkdir(parents=True)
    blocker = project / 'code' / f'historical{suffix}'
    original = b'Original source: CITATION_TO_CLEAN\n'
    blocker.write_bytes(original)
    tasks = project / 'tasks.md'
    tasks.write_text('- [ ] T001 Write requested results\n')
    ctx = SimpleNamespace(project_dir=project, project_id=project.name)
    state = {'feature_dir': str(project / 'specs/001-test'), 'tasks_path': str(tasks),
             'next_task_id': 'T001', 'all_complete': False, 'skip_llm': False}
    response = SimpleNamespace(text=('verdict: completed\nartifacts:\n'
        f'  - path: code/historical{suffix}/result.txt\n    contents: real output\n'
        '  - path: data/report.md\n    contents: New report CITATION_TO_CLEAN\n'))
    outputs = ImplementerAgent().write_artifacts(ctx, state, response)
    archive = next(path for path in (project / '.specify/recovered-artifacts').rglob(f'historical{suffix}')
                   if path.is_file())
    archive_rel = str(archive.relative_to(tmp_path))
    assert archive.read_bytes() == original
    assert archive_rel in outputs
    cleaned_paths = []
    validated_paths = []

    def clean(text, *, artifact_path, **kwargs):
        cleaned_paths.append(artifact_path)
        return (text.replace('CITATION_TO_CLEAN', '[UNVERIFIED]'),
                SimpleNamespace(flagged_count=int('CITATION_TO_CLEAN' in text)))

    monkeypatch.setattr('llmxive.agents.citation_guard.verify_and_clean', clean)
    monkeypatch.setattr('llmxive.agents.reference_validator.validate_artifact',
                        lambda **kwargs: validated_paths.append(kwargs['artifact_path']))
    # This is exactly the next production operation after write_artifacts in run.
    _validate_artifact_citations(ctx, outputs)

    assert archive.read_bytes() == original
    assert archive_rel not in cleaned_paths
    assert archive_rel not in validated_paths
    assert (project / 'data/report.md').read_text() == 'New report [UNVERIFIED]'
    assert str((project / 'data/report.md').relative_to(tmp_path)) in validated_paths


def test_redirected_archive_root_cannot_exempt_scientific_output(tmp_path, monkeypatch):
    project = tmp_path / 'projects/PROJ-999-archive-preservation'
    (project / 'data').mkdir(parents=True)
    (project / '.specify').mkdir()
    (project / '.specify/recovered-artifacts').symlink_to(project / 'data', target_is_directory=True)
    tasks = project / 'tasks.md'
    tasks.write_text('- [ ] T001 Write requested results\n')
    ctx = SimpleNamespace(project_dir=project, project_id=project.name)
    state = {'feature_dir': str(project / 'specs/001-test'), 'tasks_path': str(tasks),
             'next_task_id': 'T001', 'all_complete': False, 'skip_llm': False}
    response = SimpleNamespace(text=('verdict: completed\nartifacts:\n'
        '  - path: data/report.md\n    contents: New report CITATION_TO_CLEAN\n'))
    outputs = ImplementerAgent().write_artifacts(ctx, state, response)
    monkeypatch.setattr('llmxive.agents.citation_guard.verify_and_clean',
        lambda text, **kwargs: (text.replace('CITATION_TO_CLEAN', '[UNVERIFIED]'),
                               SimpleNamespace(flagged_count=int('CITATION_TO_CLEAN' in text))))
    monkeypatch.setattr('llmxive.agents.reference_validator.validate_artifact', lambda **kwargs: None)
    _validate_artifact_citations(ctx, outputs)
    assert (project / 'data/report.md').read_text() == 'New report [UNVERIFIED]'
