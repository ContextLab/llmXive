"""Data‑hygiene utilities (Task T013).

This module implements the project‑wide checksum and reproducibility policy:
1. SHA-256 checksums are computed for every file under the ``data/`` directory.
2. Checksums and provenance notes are recorded in ``data/metadata.yaml``.
3. Raw files (under ``data/raw/``) are enforced as immutable; if a raw file's
   checksum changes between runs, a RuntimeError is raised.
4. Each transformation is expected to write a new file with a distinct name
   to avoid overwriting intermediate results.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from llmxive_toolkit import paths

def _checksum(file_path: Path) -> str:
    """Return the SHA‑256 checksum of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _get_provenance(rel_path: str) -> str:
    """Determine provenance note based on the file path."""
    if "data/raw/" in rel_path:
        return "Raw data extraction"
    if "data/gold/" in rel_path:
        return "Human annotation"
    if "data/generated/" in rel_path:
        return "LLM generation"
    if "data/intermediate/" in rel_path:
        return "Entity extraction"
    if "data/processed/" in rel_path:
        return "Fidelity scoring"
    if "results/" in rel_path:
        return "Statistical analysis / Visualization"
    return "Pipeline artifact"

def update_all_metadata() -> None:
    """Re‑compute checksums for every file under the ``data`` folder.

    The resulting mapping is written to ``data/metadata.yaml``.
    Enforces that files in ``data/raw/`` are never overwritten.
    """
    data_root: Path = paths.root / "data"
    metadata_path: Path = paths.data("metadata.yaml")
    
    # Load existing metadata to enforce raw file immutability
    old_metadata: dict[str, Any] = {}
    if metadata_path.is_file():
        with metadata_path.open("r", encoding="utf-8") as f:
            old_metadata = yaml.safe_load(f) or {}

    new_metadata: dict[str, dict[str, str]] = {}

    for file_path in data_root.rglob("*"):
        if not file_path.is_file():
            continue
        
        rel_path = str(file_path.relative_to(paths.root))
        current_hash = _checksum(file_path)
        
        # Enforce immutability for raw files
        if "data/raw/" in rel_path and rel_path in old_metadata:
            # Handle both flat (old) and structured (new) metadata formats
            old_entry = old_metadata[rel_path]
            old_hash = old_entry["checksum"] if isinstance(old_entry, dict) else old_entry
            if current_hash != old_hash:
                raise RuntimeError(
                    f"Data hygiene violation: Raw file {rel_path} has been overwritten. "
                    f"Expected {old_hash}, found {current_hash}."
                )

        new_metadata[rel_path] = {
            "checksum": current_hash,
            "provenance": _get_provenance(rel_path)
        }

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(new_metadata, f, sort_keys=False)
