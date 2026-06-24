"""
Utility for computing and tracking checksums of data artifacts.

This module provides a lightweight, thread‑safe manifest that records the
cryptographic hash (SHA‑256 by default) of any file that participates in the
pipeline.  The manifest lives in ``data/analysis/artifact_hashes.json`` and
can be queried or updated from any part of the code base.

Typical usage:

>>> from checksum_manifest import record_artifact, verify_artifact
>>> checksum = record_artifact(Path("data/processed/clone_metrics.csv"))
>>> is_valid = verify_artifact(Path("data/processed/clone_metrics.csv"))
"""

import hashlib
import json
from pathlib import Path
from threading import RLock
from typing import Dict, Optional

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Default location for the manifest file.  ``Path(__file__)`` points to the
# ``code`` directory; we step up two levels to the project root and then
# into ``data/analysis``.
_DEFAULT_MANIFEST: Path = (
    Path(__file__).parents[2] / "data" / "analysis" / "artifact_hashes.json"
)
_LOCK = RLock()

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the hexadecimal digest of *file_path* using *algorithm*.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum should be calculated.
    algorithm: str, optional
        Name of the hashlib algorithm (default ``'sha256'``).

    Returns
    -------
    str
        Hexadecimal hash string.
    """
    file_path = Path(file_path)
    hasher = hashlib.new(algorithm)
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def _load_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Load the JSON manifest from *manifest_path*.

    If the file does not exist or is malformed, an empty dict is returned.
    """
    if manifest_path.is_file():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}

def _save_manifest(manifest: Dict[str, str], manifest_path: Path) -> None:
    """
    Persist *manifest* to *manifest_path* in a pretty‑printed JSON format.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def record_artifact(
    file_path: Path,
    manifest_path: Optional[Path] = None,
    algorithm: str = "sha256",
) -> str:
    """
    Compute the checksum of *file_path* and store it in the manifest.

    Parameters
    ----------
    file_path: Path
        The file to hash.
    manifest_path: Path, optional
        Override the default manifest location.
    algorithm: str, optional
        Hash algorithm to use (default ``'sha256'``).

    Returns
    -------
    str
        The computed checksum.
    """
    file_path = Path(file_path)
    manifest_path = Path(manifest_path) if manifest_path else _DEFAULT_MANIFEST
    checksum = compute_hash(file_path, algorithm)

    with _LOCK:
        manifest = _load_manifest(manifest_path)
        manifest[str(file_path)] = checksum
        _save_manifest(manifest, manifest_path)

    return checksum

def get_recorded_hash(
    file_path: Path,
    manifest_path: Optional[Path] = None,
) -> Optional[str]:
    """
    Retrieve the stored checksum for *file_path* if it exists.

    Returns ``None`` when the file is not present in the manifest.
    """
    file_path = Path(file_path)
    manifest_path = Path(manifest_path) if manifest_path else _DEFAULT_MANIFEST
    with _LOCK:
        manifest = _load_manifest(manifest_path)
    return manifest.get(str(file_path))

def verify_artifact(
    file_path: Path,
    manifest_path: Optional[Path] = None,
    algorithm: str = "sha256",
) -> bool:
    """
    Re‑compute the checksum of *file_path* and compare it to the stored value.

    Returns ``True`` if the current hash matches the recorded one, otherwise
    ``False`` (including the case where no entry exists).
    """
    recorded = get_recorded_hash(file_path, manifest_path)
    if recorded is None:
        return False
    current = compute_hash(file_path, algorithm)
    return current == recorded

__all__ = [
    "compute_hash",
    "record_artifact",
    "get_recorded_hash",
    "verify_artifact",
]