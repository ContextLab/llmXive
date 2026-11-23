"""Immutable behavioral checks run separately on every repair candidate.

Existing project content must remain recoverable, even when a file occupies a
path that a scaffold expects to be a directory. A safe migration may move it to
a project-local backup; silently deleting it is never an accepted repair.
"""
from types import SimpleNamespace

import pytest

from llmxive.speckit.implement_cmd import ImplementerAgent
from llmxive.speckit.runner import init_speckit_in


@pytest.mark.parametrize('relative', ['code', 'src', 'scripts', '.specify/templates'])
@pytest.mark.parametrize('payload', [b'(Directory created)\n', b'Unique existing research content\x00\xff\n'])
def test_scaffolding_preserves_existing_content(tmp_path, relative, payload):
    project=tmp_path/'projects/PROJ-preservation'
    blocked=project/relative
    blocked.parent.mkdir(parents=True)
    blocked.write_bytes(payload)
    try:
        init_speckit_in(project)
    except OSError:
        # Refusing a collision is safe; reconciliation may archive it instead.
        pass
    copies=[p for p in project.rglob('*') if p.is_file() and not p.is_symlink()
            and p.read_bytes()==payload]
    assert copies, f'Existing bytes at {relative} were lost instead of preserved'


@pytest.mark.parametrize('relative', ['code', 'data/processed', 'src/config'])
@pytest.mark.parametrize('link', [False, True])
def test_implementation_writer_preserves_collision_and_existing_backups(tmp_path, relative, link):
    """Exercise the observed writer, including occupied backup names and symlinks."""
    project = tmp_path/'projects/PROJ-preservation'
    blocker = project/relative
    blocker.parent.mkdir(parents=True)
    payload = b'Current research bytes\x00\xff\n'
    outside = tmp_path/'external-research'
    outside.write_bytes(payload)
    if link:
        blocker.symlink_to(outside)
    else:
        blocker.write_bytes(payload)
    # Both backup conventions appeared in real rejected proposals. Distinct
    # payloads ensure overwriting/deleting a previous backup cannot pass.
    backups = [blocker.with_suffix('.bak'), blocker.with_name(blocker.name+'.placeholder.txt')]
    expected = [payload]
    for index, backup in enumerate(backups):
        content = f'Prior backup {index}\n'.encode() + b'\x00\xfe'
        backup.write_bytes(content)
        expected.append(content)
    tasks = project/'tasks.md'
    tasks.write_text('- [ ] T001 Write artifact\n')
    context = SimpleNamespace(project_dir=project, project_id=project.name)
    mechanical = {'feature_dir': str(project/'specs/001-preservation'),
                  'tasks_path': str(tasks), 'next_task_id': 'T001',
                  'all_complete': False, 'skip_llm': False}
    response = SimpleNamespace(text=(
        'verdict: completed\nartifacts:\n'
        f'  - path: {relative}/result.txt\n    contents: actual result\n'))
    try:
        ImplementerAgent().write_artifacts(context, mechanical, response)
    except OSError:
        pass  # Refusing a collision is safe; byte deletion is not.
    copies = [p.read_bytes() for p in project.rglob('*') if p.is_file() and not p.is_symlink()]
    for content in expected[1:] if link else expected:
        assert content in copies, f'Writer lost existing content at {relative}'
    assert outside.read_bytes() == payload
    if link:
        assert any(p.is_symlink() and p.readlink() == outside for p in project.rglob('*'))
