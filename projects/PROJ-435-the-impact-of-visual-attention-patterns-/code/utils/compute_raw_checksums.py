"""
Script that computes SHA‑256 hashes for all ``*.parquet`` files under
``data/raw`` and records them in ``state/artifacts.yaml``.

This script is intended to be run after the raw eye‑tracking dataset has
been downloaded (Task T005). It uses the public helper functions from
``code_08_verify_artifacts_checksums.py``.
"""
import logging
from pathlib import Path

import yaml

from llmxive_toolkit import paths, get_logger

# Import the checksum utilities defined in the sibling module
from code_08_verify_artifacts_checksums import (
    compute_sha256,
    get_project_root,
    load_hash_registry,
    save_hash_registry,
)

log = get_logger(__name__)

def main() -> None:
    """
    Locate all ``*.parquet`` files in ``data/raw``, compute their SHA‑256
    hashes, and write the mapping to ``state/artifacts.yaml``.
    """
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"

    parquet_files = list(raw_dir.glob("*.parquet"))
    if not parquet_files:
        log.warning("No parquet files found in %s; nothing to checksum.", raw_dir)
        return

    # Load any existing registry so we preserve entries for other files
    registry = load_hash_registry()

    for parquet_path in parquet_files:
        rel_path = str(parquet_path.relative_to(project_root))
        try:
            file_hash = compute_sha256(parquet_path)
            registry[rel_path] = file_hash
            log.info("Checksum for %s: %s", rel_path, file_hash)
        except IOError as exc:
            log.error("Failed to read %s: %s", parquet_path, exc)
            raise

    # Persist the updated registry
    artifacts_path = project_root / "state" / "artifacts.yaml"
    artifacts_path.parent.mkdir(parents=True, exist_ok=True)
    with artifacts_path.open("w") as f:
        yaml.safe_dump(registry, f)
    log.info("Wrote %d checksum entries to %s", len(registry), artifacts_path)

if __name__ == "__main__":
    main()
