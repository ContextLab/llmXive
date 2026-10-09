"""Immutable behavioral checks run separately on every repair candidate.

Existing project content must remain recoverable, even when a file occupies a
path that a scaffold expects to be a directory. A safe migration may move it to
a project-local backup; silently deleting it is never an accepted repair.
"""
from pathlib import Path

import pytest

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
