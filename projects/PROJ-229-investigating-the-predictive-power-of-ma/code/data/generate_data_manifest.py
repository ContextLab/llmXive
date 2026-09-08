"""
generate_data_manifest.py

This script creates a manifest JSON file describing the raw input datasets
and the target decision file produced by the earlier pipeline steps.
The manifest is written to ``data/results/data_manifest.json`` and includes
for each file:

- Relative path (POSIX style)
- File size in bytes
- SHA256 checksum (computed using the project's checksum utility)

The script is deliberately lightweight and does not attempt to
re‑download or synthesize any data; it will raise an exception if any of the
expected source files are missing, ensuring that the pipeline fails loudly
when required inputs are unavailable.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# Project‑wide logger utility
from utils.logger import get_pipeline_logger

# Checksum utility provided elsewhere in the repository
from utils.checksum import compute_sha256

logger = get_pipeline_logger(__name__)

# ----------------------------------------------------------------------
# Configuration – paths are relative to the repository root.
# ----------------------------------------------------------------------
RAW_MATERIALS_PATH = Path("data/raw/materials_project_data.json")
RAW_NIST_PATH = Path("data/raw/nist_data.json")
TARGET_DECISION_PATH = Path("data/results/target_decision.json")
MANIFEST_OUTPUT_PATH = Path("data/results/data_manifest.json")

def _file_record(file_path: Path) -> dict:
    """
    Build a dictionary with metadata for *file_path*.

    Parameters
    ----------
    file_path: Path
        Path to the file whose information should be recorded.

    Returns
    -------
    dict
        ``{'path': <relative posix string>, 'size_bytes': <int>,
         'sha256': <hex string>}``
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Required file not found: {file_path}")

    size = file_path.stat().st_size
    checksum = compute_sha256(file_path)

    logger.debug(
        "Recorded file %s – size: %d bytes, sha256: %s",
        file_path,
        size,
        checksum,
    )

    return {
        "path": file_path.as_posix(),
        "size_bytes": size,
        "sha256": checksum,
    }

def generate_manifest() -> dict:
    """
    Assemble the manifest dictionary and write it to disk.

    Returns
    -------
    dict
        The manifest dictionary that was written.
    """
    logger.info("Generating data manifest...")

    files = [
        _file_record(RAW_MATERIALS_PATH),
        _file_record(RAW_NIST_PATH),
        _file_record(TARGET_DECISION_PATH),
    ]

    manifest = {
        "manifest_version": 1,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "files": files,
    }

    # Ensure the output directory exists
    MANIFEST_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with MANIFEST_OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=False)

    logger.info(
        "Data manifest written to %s (contains %d entries)",
        MANIFEST_OUTPUT_PATH,
        len(files),
    )
    return manifest

def main() -> None:
    """
    Entry‑point for ``python -m code.data.generate_data_manifest``.
    """
    try:
        generate_manifest()
    except Exception as exc:
        logger.error("Failed to generate data manifest: %s", exc, exc_info=True)
        raise

if __name__ == "__main__":
    # When executed as a script ``python code/data/generate_data_manifest.py``,
    # run the main routine.
    main()