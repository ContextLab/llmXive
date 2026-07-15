"""Shared atomic state-file I/O (issue #1139 / Constitution I).

Before this module, only ``publication.py`` and ``revision_history.py`` wrote
state atomically, each with its own private ``_atomic_write`` copy; every other
state store did a bare ``path.write_text(...)`` — a crash mid-write truncates the
JSON/YAML and the next ``load()`` reads ``{}`` or raises. Two overlapping pipeline
ticks (different HEADs, same project) could also silently lose an update because
the read-modify-write stores had no compare-and-swap.

This is the ONE shared helper all state stores route through: a temp file in the
destination directory written and ``os.replace``-d into place (atomic on POSIX),
plus an optional mtime-based compare-and-swap for read-modify-write callers.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write ``content`` to ``path`` atomically (temp file + ``os.replace``).

    A reader either sees the complete previous file or the complete new file,
    never a truncated one. Parent directories are created as needed.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


class StaleWriteError(RuntimeError):
    """Raised by :func:`atomic_write_text_cas` when the file changed on disk
    since the caller last read it (lost-update guard for read-modify-write
    stores mutated by concurrent pipeline ticks)."""


def read_mtime_ns(path: Path) -> int | None:
    """Return the file's mtime in ns, or ``None`` if it does not exist. Callers
    capture this before a read-modify-write and pass it to
    :func:`atomic_write_text_cas` as the expected version token."""
    try:
        return Path(path).stat().st_mtime_ns
    except FileNotFoundError:
        return None


def atomic_write_text_cas(
    path: Path,
    content: str,
    *,
    expected_mtime_ns: int | None,
    encoding: str = "utf-8",
) -> None:
    """Atomic write that first verifies the on-disk file still matches the
    ``expected_mtime_ns`` captured before the read-modify-write. If another
    writer landed in between, raise :class:`StaleWriteError` so the caller can
    re-read and retry instead of clobbering the newer state.
    """
    path = Path(path)
    current = read_mtime_ns(path)
    if current != expected_mtime_ns:
        raise StaleWriteError(
            f"{path} changed since read (expected mtime {expected_mtime_ns}, "
            f"found {current}); refusing to overwrite newer state"
        )
    atomic_write_text(path, content, encoding=encoding)
