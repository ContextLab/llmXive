"""Bounded, read-only active-feature inputs promised by research task review."""
from __future__ import annotations

import os
import stat
from pathlib import Path

MAX_FILES = 32
MAX_ENTRIES = 256
MAX_FILE_BYTES = 64 * 1024
MAX_TOTAL_BYTES = 128 * 1024


def task_contract_context(feature_dir: Path, project_dir: Path) -> str:
    """Read optional data-model.md and contracts/**, never another feature/tree.

    Absent inputs are valid. Unsafe, unreadable, non-text or oversized inputs
    fail explicitly: silently dropping a contract could authorize an incomplete
    analysis. These inputs are context, not artifacts the task reviser may edit.
    """
    root = project_dir.resolve(strict=True)
    feature = feature_dir.absolute()

    def reject(path: Path, reason: str) -> ValueError:
        return ValueError(f"Task review context refused {path.name!r}: {reason}. "
                          "Repair the active feature input before retrying task review.")

    try:
        relative = feature.relative_to(project_dir.absolute())
        feature = root / relative
        cursor = root
        for part in relative.parts:
            cursor /= part
            if cursor.is_symlink():
                raise reject(cursor, 'symlinked feature paths are not supported')
        feature.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        raise reject(feature, 'feature must be a real directory inside its project') from exc

    files: list[Path] = []
    pending = [feature / 'data-model.md', feature / 'contracts']
    entries = 0
    total = 0
    sections = []
    while pending:
        path = pending.pop()
        try:
            info = path.lstat()
        except FileNotFoundError:
            if path.parent == feature:
                continue  # Optional absent data-model / contracts directory.
            raise reject(path, 'input disappeared while building the review packet') from None
        except OSError as exc:
            raise reject(path, 'input could not be inspected') from exc
        entries += 1
        if entries > MAX_ENTRIES:
            raise reject(path, f'input tree exceeds {MAX_ENTRIES} entries')
        if stat.S_ISLNK(info.st_mode):
            raise reject(path, 'symlinked context files/directories are not supported')
        if stat.S_ISDIR(info.st_mode) and path != feature / 'data-model.md':
            try:
                with os.scandir(path) as children:
                    for child in children:
                        if entries + len(pending) >= MAX_ENTRIES:
                            raise reject(path, f'input tree exceeds {MAX_ENTRIES} entries')
                        pending.append(Path(child.path))
            except OSError as exc:
                raise reject(path, 'directory could not be read') from exc
            continue
        if path == feature / "contracts":
            raise reject(path, "contracts must be a directory")
        if not stat.S_ISREG(info.st_mode):
            raise reject(path, 'expected a regular text file')
        files.append(path)
        if len(files) > MAX_FILES:
            raise reject(path, f'input set exceeds {MAX_FILES} files')
    for path in sorted(files):
        try:
            with path.open('rb') as stream:
                body = stream.read(MAX_FILE_BYTES + 1)
        except OSError as exc:
            raise reject(path, 'file could not be read') from exc
        total += len(body)
        if len(body) > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
            raise reject(path, f'contract budget exceeded ({MAX_FILE_BYTES} bytes/file, '
                         f'{MAX_TOTAL_BYTES} bytes total); split or compact inputs without dropping requirements')
        try:
            content = body.decode('utf-8')
        except UnicodeError as exc:
            raise reject(path, 'expected UTF-8 text') from exc
        if '\x00' in content:
            raise reject(path, 'binary content is not reviewable text')
        sections.append(f"## {path.relative_to(project_dir.resolve()).as_posix()}\n\n{content}")
    if not sections:
        return ''
    return '# Active data model and contracts (read-only requirements)\n\n' + '\n\n'.join(sections)
