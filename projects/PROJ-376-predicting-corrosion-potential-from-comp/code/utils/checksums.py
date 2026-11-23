"""
checksums.py
------------

Generate SHA-256 checksums for all files under ``data/raw/`` and record them in a
project-owned manifest file ``data/logs/raw_checksums.yaml``.

This script satisfies the requirement to track raw data integrity while adhering
to the constraint that the ``state/`` directory is platform-owned and must not
be written to by project code.

The manifest file is a YAML document with a top-level ``artifact_hashes`` mapping:

.. code-block:: yaml

    artifact_hashes:
      data/raw/file1.csv: <sha256>
      data/raw/subdir/file2.zip: <sha256>
"""
import hashlib
import yaml
from pathlib import Path
from typing import Dict
from llmxive_toolkit import paths

__all__ = ["generate_checksums"]

def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of ``file_path``."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_checksums(
    raw_root: Path = paths.data("raw"),
    state_file: Path = paths.logs("raw_checksums.yaml"),
) -> None:
    """
    Walk ``raw_root`` (recursively), compute SHA-256 checksums for every regular file,
    and store the mapping in ``state_file`` under the ``artifact_hashes`` key.

    The function creates any missing parent directories, merges with an existing
    manifest file (preserving other keys), and overwrites the ``artifact_hashes``
    map with the newly computed entries.

    Parameters
    ----------
    raw_root: Path
        Root directory containing raw artefacts. Defaults to ``data/raw``.
    state_file: Path
        YAML file where the checksum map is persisted. Defaults to
        ``data/logs/raw_checksums.yaml``.
    """
    # Ensure the raw directory exists
    raw_root.mkdir(parents=True, exist_ok=True)

    # Compute hashes
    hashes: Dict[str, str] = {}
    for path in raw_root.rglob("*"):
        if path.is_file():
            # Store POSIX style path relative to project root for consistency
            # We calculate the path relative to the project root
            try:
                rel_path = path.relative_to(paths.root).as_posix()
            except ValueError:
                rel_path = path.as_posix()
            hashes[rel_path] = _compute_sha256(path)

    # Load (or create) the existing manifest YAML
    state_file.parent.mkdir(parents=True, exist_ok=True)
    if state_file.exists():
        with state_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    # Update the artifact_hashes map
    data.setdefault("artifact_hashes", {})
    data["artifact_hashes"].update(hashes)

    # Write back to YAML
    with state_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)

if __name__ == "__main__":
    # When executed as a script, run the checksum generation with defaults.
    generate_checksums()
