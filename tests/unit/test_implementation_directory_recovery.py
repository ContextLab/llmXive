"""Observed implementation writer collisions must recover without losing bytes."""
from types import SimpleNamespace

import pytest

from llmxive.speckit._artifact_directories import prepare_artifact_directory
from llmxive.speckit.implement_cmd import ImplementerAgent


def invoke(project, relative):
    tasks = project / 'tasks.md'
    tasks.write_text('- [ ] T001 Write the requested result\n')
    ctx = SimpleNamespace(project_dir=project, project_id=project.name)
    state = {'feature_dir': str(project / 'specs/001-test'), 'tasks_path': str(tasks),
             'next_task_id': 'T001', 'all_complete': False, 'skip_llm': False}
    response = SimpleNamespace(text=('verdict: completed\nartifacts:\n'
        f'  - path: {relative}/result.txt\n    contents: actual result\n'))
    return ImplementerAgent().write_artifacts(ctx, state, response)


@pytest.mark.parametrize('relative', ['code', 'data/processed', 'src/config'])
@pytest.mark.parametrize('payload', [b'(Directory created)\n', b'Research bytes\x00\xff\n'])
def test_existing_writer_recovers_directory_collision_and_preserves_backups(tmp_path, relative, payload):
    project = tmp_path / 'projects/PROJ-770-collision'
    blocker = project / relative
    blocker.parent.mkdir(parents=True)
    blocker.write_bytes(payload)
    backup = blocker.with_suffix('.bak')
    backup.write_bytes(b'Older distinct bytes\x00\xfe\n')

    written = invoke(project, relative)

    assert blocker.is_dir()
    assert (blocker / 'result.txt').read_text() == 'actual result'
    assert backup.read_bytes() == b'Older distinct bytes\x00\xfe\n'
    recovered = [p for p in (project / '.specify/recovered-artifacts').rglob('*')
                 if p.is_file() and p.read_bytes() == payload]
    assert len(recovered) == 1
    assert str(recovered[0].relative_to(tmp_path)) in written
    invoke(project, relative)
    assert recovered[0].read_bytes() == payload
    assert len([p for p in (project / '.specify/recovered-artifacts').rglob('*')
                if p.is_file() and p.read_bytes() == payload]) == 1


@pytest.mark.parametrize('relative', ['.specify', '.specify/recovered-artifacts'])
def test_recovery_refuses_redirected_archive_without_moving_original(tmp_path, relative):
    project = tmp_path / 'projects/PROJ-770-collision'
    project.mkdir(parents=True)
    blocker = project / 'code'
    blocker.write_bytes(b'Original binary\x00\xff')
    outside = tmp_path / 'outside'
    outside.mkdir()
    link = project / relative
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(FileExistsError):
        invoke(project, 'code')
    assert blocker.read_bytes() == b'Original binary\x00\xff'
    assert list(outside.iterdir()) == []
    assert link.is_symlink()


def test_nonregular_blocker_is_preserved_and_never_followed(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (project / 'code').symlink_to(outside, target_is_directory=True)
    with pytest.raises(FileExistsError):
        prepare_artifact_directory(project, project / 'code/.tasks')
    assert (project / 'code').is_symlink()
    assert list(outside.iterdir()) == []


def test_outside_directory_is_refused(tmp_path):
    project = tmp_path / 'project'
    project.mkdir()
    with pytest.raises(ValueError):
        prepare_artifact_directory(project, tmp_path / 'outside')
    assert not (tmp_path / 'outside').exists()


def test_parent_alias_preserves_caller_path_identity(tmp_path):
    original = tmp_path / 'actual'
    original.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(original, target_is_directory=True)
    project = alias / 'projects/PROJ-770-collision'
    project.mkdir(parents=True)
    (project / 'code').write_bytes(b'original')
    written = invoke(project, 'code')
    assert any('/.specify/recovered-artifacts/' in path for path in written)


def test_refusal_logging_recovers_code_but_leaves_task_incomplete(tmp_path):
    project = tmp_path / 'projects/PROJ-770-collision'
    project.mkdir(parents=True)
    (project / 'code').write_bytes(b'Original content')
    # A rejected output still needs its production diagnostic log directory.
    invoke(project, '../escape')
    assert '- [ ] T001' in (project / 'tasks.md').read_text()
    assert (project / 'code/.tasks/T001.artifact-write.log').is_file()
    assert any(p.read_bytes() == b'Original content' for p in
               (project / '.specify/recovered-artifacts').rglob('*') if p.is_file())
    assert not (project.parent / 'escape').exists()
