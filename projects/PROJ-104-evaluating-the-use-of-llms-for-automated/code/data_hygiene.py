"""Data‑hygiene utilities (Task T013).

This module implements the project‑wide checksum policy:
* After any pipeline stage finishes, ``update_all_metadata`` walks the
  entire ``data/`` directory, computes a SHA‑256 checksum for each file,
  and writes (or overwrites) ``data/metadata.yaml`` with a mapping from
  *relative* file paths (relative to the project root) to their checksums.
* The function is deliberately side‑effect‑only – it does **not** attempt
  to modify any existing data files, thereby enforcing the “raw files are
  never overwritten” rule.
* Individual scripts (e.g. ``code/data_extraction.py`` and
  ``code/gold_annotation.py``) may still call their own ``update_metadata``
  helper for immediate provenance; ``update_all_metadata`` simply ensures
  that the final state of the ``data/`` tree is fully recorded.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from llmxive_toolkit import paths

def _checksum(file_path: Path) -> str:
    """Return the SHA‑256 checksum of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def update_all_metadata() -> None:
    """Re‑compute checksums for every file under the ``data`` folder.

    The resulting mapping is written to ``data/metadata.yaml``.  Existing
    entries are overwritten – this is intentional because the function
    is called **after** the pipeline has produced all artefacts, guaranteeing
    that the metadata reflects the final state.
    """
    data_root: Path = paths.root / "data"
    metadata_path: Path = paths.data("metadata.yaml")
    metadata: dict[str, str] = {}

    for file_path in data_root.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(paths.root))
            metadata[rel_path] = _checksum(file_path)

    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(metadata, f, sort_keys=False)
