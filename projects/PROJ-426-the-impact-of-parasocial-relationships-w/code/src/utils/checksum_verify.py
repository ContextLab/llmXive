"""
Verification utility for the checksum manifest produced by
``src.utils.checksum``. It recomputes the SHA‑256 hash of every file
listed in ``data/artifact_manifest.yaml`` and raises an exception if
any checksum differs or if a listed file is missing.

The script exits with status 0 when all checks pass; otherwise it
raises a ``RuntimeError`` and logs details.
"""

import sys
from pathlib import Path
from typing import Dict

import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def load_manifest(manifest_path: Path) -> Dict[str, str]:
    """Load the YAML manifest mapping relative paths to expected checksums."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Manifest content is not a mapping")
    return data

def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file (duplicate of the function in checksum.py)."""
    import hashlib

    hash_sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def verify_checksums(root_data_dir: Path, manifest: Dict[str, str]) -> None:
    """
    Verify that each file listed in ``manifest`` exists under ``root_data_dir``
    and that its checksum matches the recorded value.

    Raises
    ------
    RuntimeError
        If any file is missing or its checksum does not match.
    """
    errors = []
    for rel_path, expected_checksum in manifest.items():
        # ``rel_path`` is expected to start with ``data/``; strip that prefix
        if not rel_path.startswith("data/"):
            errors.append(f"Invalid manifest entry (must start with 'data/'): {rel_path}")
            continue
        # Resolve the absolute path
        absolute_path = paths.root / rel_path
        if not absolute_path.is_file():
            errors.append(f"Missing file: {rel_path}")
            continue
        actual_checksum = compute_sha256(absolute_path)
        if actual_checksum != expected_checksum:
            errors.append(
                f"Checksum mismatch for {rel_path}: expected {expected_checksum}, got {actual_checksum}"
            )
    if errors:
        for err in errors:
            log.error(err)
        raise RuntimeError("Checksum verification failed; see log for details")
    else:
        log.info("All artifact checksums verified successfully.")

def main() -> int:
    """CLI entry point."""
    manifest_path = paths.data("artifact_manifest.yaml")
    data_dir = paths.data()
    try:
        manifest = load_manifest(manifest_path)
        verify_checksums(data_dir, manifest)
        print("Checksum verification passed.")
        return 0
    except Exception as e:
        print(f"Checksum verification failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
