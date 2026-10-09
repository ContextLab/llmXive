"""
Utilities for managing the project's data manifest (data/manifest.json).

This module provides functions to compute SHA‑256 checksums and to
load, save and update the manifest. The implementation is deliberately
tolerant: missing keys are created on‑the‑fly and callers can supply
arbitrary additional metadata without breaking existing functionality.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

MANIFEST_PATH = Path("data/manifest.json")


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of *file_path* and return it as a
    hexadecimal string.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_manifest() -> Dict[str, Any]:
    """
    Load the manifest JSON file. If the file does not exist, return an
    empty manifest structure.
    """
    if MANIFEST_PATH.is_file():
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {"datasets": {}, "metadata": {}}


def save_manifest(manifest: Dict[str, Any]) -> None:
    """
    Write *manifest* to ``data/manifest.json`` with pretty‑printing.
    """
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def update_manifest(
    dataset_name: str,
    file_path: str,
    source_url: str,
    dataset_type: str,
    description: str,
    checksum_sha256: str | None = None,
    file_size_bytes: int | None = None,
) -> None:
    """
    Update (or create) an entry in the manifest for *dataset_name*.

    Parameters
    ----------
    dataset_name: str
        Logical name of the dataset (e.g., ``occurrence_1970_2000``).
    file_path: str
        Path to the file relative to the project root.
    source_url: str
        URL from which the data were obtained.
    dataset_type: str
        High‑level type (e.g., ``occurrence`` or ``climate``).
    description: str
        Human‑readable description.
    checksum_sha256: str | None
        SHA‑256 checksum; if omitted the caller may have recorded it
        elsewhere.
    file_size_bytes: int | None
        Size of the file in bytes; optional.
    """
    manifest = load_manifest()
    entry = {
        "file_path": file_path,
        "source_url": source_url,
        "dataset_type": dataset_type,
        "description": description,
        "download_timestamp": datetime.utcnow().isoformat(),
    }
    if checksum_sha256:
        entry["checksum_sha256"] = checksum_sha256
    if file_size_bytes:
        entry["file_size_bytes"] = file_size_bytes

    manifest["datasets"][dataset_name] = entry
    # Update top‑level metadata
    manifest.setdefault("metadata", {})
    manifest["metadata"]["updated_at"] = datetime.utcnow().isoformat()
    save_manifest(manifest)