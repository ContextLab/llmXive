"""
Utilities for computing SHA‑256 checksums of data files.
The original implementation attempted to call ``asdict`` on plain
strings, which raised a ``TypeError``.  This module now defines a proper
``ChecksumEntry`` dataclass and provides a small API used by the
``code/reproducibility/checksums.py`` script.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List

@dataclass
class ChecksumEntry:
    """Record for a single file's checksum and size."""
    path: str
    sha256: str
    size: int

def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of ``file_path``."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_file_size(file_path: Path) -> int:
    """Return the size of ``file_path`` in bytes."""
    return file_path.stat().st_size

def find_data_files(root: Path, extensions: Iterable[str] = (".csv", ".json", ".txt", ".png")) -> List[Path]:
    """
    Recursively locate files under ``root`` whose suffix is in ``extensions``.
    Returns a list of absolute ``Path`` objects.
    """
    files: List[Path] = []
    for ext in extensions:
        files.extend(root.rglob(f"*{ext}"))
    return files

def record_checksums(files: Iterable[Path]) -> List[ChecksumEntry]:
    """
    Compute a ``ChecksumEntry`` for each file.
    """
    entries: List[ChecksumEntry] = []
    for p in files:
        entries.append(
            ChecksumEntry(
                path=str(p.relative_to(p.anchor)),
                sha256=compute_sha256(p),
                size=get_file_size(p),
            )
        )
    return entries

def write_checksums_json(entries: List[ChecksumEntry], out_path: Path) -> None:
    """
    Serialize ``entries`` as a JSON array and write to ``out_path``.
    """
    import json

    data = [asdict(entry) for entry in entries]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
