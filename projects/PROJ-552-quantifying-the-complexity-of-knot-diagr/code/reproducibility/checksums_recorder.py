"""
Utility module for checksum recording.

Provides dataclasses and helper functions used by ``code/reproducibility/checksums.py``.
This file existed previously but lacked a concrete implementation for some
helpers that were referenced elsewhere.  The implementation below is
self‑contained and does not depend on external packages beyond the Python
standard library.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List

@dataclass
class ChecksumEntry:
    """
    Represents a checksum record for a single file.

    Attributes
    ----------
    relative_path: str
        Path of the file relative to the ``data`` directory.
    checksum: str
        Hexadecimal SHA‑256 digest.
    size: int
        File size in bytes.
    """
    relative_path: str
    checksum: str
    size: int

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def get_file_size(file_path: Path) -> int:
    """Return the size of *file_path* in bytes."""
    return file_path.stat().st_size

def find_data_files(root: Path) -> List[Path]:
    """
    Recursively find all regular files under *root*.

    Returns
    -------
    List[Path]
        List of absolute ``Path`` objects for each file found.
    """
    return [p for p in root.rglob("*") if p.is_file()]

def record_checksums(entries: Iterable[ChecksumEntry]) -> List[ChecksumEntry]:
    """
    Placeholder for future extensions (e.g., database storage).

    Currently returns the entries unchanged.
    """
    return list(entries)

def write_checksums_json(entries: Iterable[ChecksumEntry], output_path: Path) -> None:
    """
    Serialize *entries* to JSON and write to *output_path*.

    The JSON format is a list of dictionaries with the keys
    ``relative_path``, ``checksum`` and ``size``.
    """
    data = [asdict(entry) for entry in entries]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")