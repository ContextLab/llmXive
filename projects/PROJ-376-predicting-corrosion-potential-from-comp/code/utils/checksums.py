"""
checksums.py
--------------

Generate SHA‑256 checksums for all files under ``data/raw/`` and record them in the
project‑level state file ``state/projects/PROJ-376-predicting-corrosion-potential-from-comp.yaml``.
The script can be invoked directly or imported; the ``generate_checksums`` function
performs the core work.

The state file is a YAML document with a top‑level ``artifact_hashes`` mapping:

.. code-block:: yaml

    artifact_hashes:
      data/raw/file1.csv: <sha256>
      data/raw/subdir/file2.zip: <sha256>
"""
import hashlib
import yaml
from pathlib import Path
from typing import Dict

__all__ = ["generate_checksums"]

def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 hash of ``file_path``."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_checksums(
    raw_root: Path = Path("data/raw"),
    state_file: Path = Path(
        "state/projects/PROJ-376-predicting-corrosion-potential-from-comp.yaml"
    ),
) -> None:
    """
    Walk ``raw_root`` (recursively), compute SHA‑256 checksums for every regular file,
    and store the mapping in ``state_file`` under the ``artifact_hashes`` key.

    The function creates any missing parent directories, merges with an existing
    state file (preserving other keys), and overwrites the ``artifact_hashes`` map
    with the newly computed entries (updating existing ones if they changed).

    Parameters
    ----------
    raw_root: Path
        Root directory containing raw artefacts. Defaults to ``data/raw``.
    state_file: Path
        YAML file where the checksum map is persisted. Defaults to the project‑level
        state file under ``state/projects``.
    """
    # Ensure the raw directory exists (no error if it already does)
    raw_root.mkdir(parents=True, exist_ok=True)

    # Compute hashes
    hashes: Dict[str, str] = {}
    for path in raw_root.rglob("*"):
        if path.is_file():
            rel_path = path.as_posix()  # store POSIX style path relative to project root
            hashes[rel_path] = _compute_sha256(path)

    # Load (or create) the existing state YAML
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
    # When executed as a script, simply run the checksum generation with defaults.
    generate_checksums()
