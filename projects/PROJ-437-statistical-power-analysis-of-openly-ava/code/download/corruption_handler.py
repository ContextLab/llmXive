"""
Corruption Handler
------------------
A tiny helper that can be used by downstream modules to detect
corrupted files based on a pre‑computed SHA‑256 hash.  The module
does **not** attempt to repair files – it raises an exception when a
mismatch is detected, adhering to the “fail loudly” policy.
"""

import hashlib
from pathlib import Path
from typing import Dict

class CorruptionError(RuntimeError):
    """Raised when a file's hash does not match the expected value."""
    pass


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 hash of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_file_integrity(file_path: Path, expected_hash: str) -> None:
    """
    Verify that ``file_path`` matches ``expected_hash``.  Raises
    ``CorruptionError`` on mismatch.
    """
    actual = compute_sha256(file_path)
    if actual.lower() != expected_hash.lower():
        raise CorruptionError(f"Hash mismatch for {file_path}: expected {expected_hash}, got {actual}")
