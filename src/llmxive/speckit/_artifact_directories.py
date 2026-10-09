"""Recover legacy file/directory collisions without discarding project content."""
from __future__ import annotations

import stat
import tempfile
from pathlib import Path


def prepare_artifact_directory(project: Path, directory: Path) -> list[Path]:
    """Make project-local parents, archiving regular blockers under control data.

    Never follow a symlink or replace an existing backup. Archives retain the
    original project-relative path inside a uniquely created recovery directory.
    This is a filesystem migration, not a scientific completion decision.
    """
    relative = directory.absolute().relative_to(project.absolute())
    if '..' in relative.parts or project.is_symlink():
        raise ValueError('Artifact directory must be inside the real project')
    root = project.resolve(strict=True)
    current = root
    recovered = []

    def regular_directory(path: Path) -> None:
        try:
            path.mkdir()
        except FileExistsError:
            if path.is_symlink() or not path.is_dir():
                raise

    for part in relative.parts:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            regular_directory(current)
            continue
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            raise FileExistsError(f'Refusing non-regular directory blocker: {current}')
        recovery = root / '.specify' / 'recovered-artifacts'
        regular_directory(recovery.parent)
        regular_directory(recovery)
        slot = Path(tempfile.mkdtemp(prefix='directory-collision-', dir=recovery))
        destination = slot / current.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        # The destination is inside a newly created empty directory. Rename
        # preserves the exact bytes, permissions and inode; no decoding/copying.
        current.rename(destination)
        current.mkdir()
        recovered.append(project / destination.relative_to(root))
    return recovered
