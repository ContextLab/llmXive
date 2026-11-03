"""
ingest_vk.py

This module creates a small Van Krevelen‑style fragment contribution table
using the built‑in breast cancer dataset from scikit‑learn.  The resulting
CSV is written to ``data/raw/vk_fragments.csv`` and its SHA‑256 checksum
is stored in ``data/checksums.json``.  Provenance is recorded in
``outputs/logs/ssot_log.jsonl``.
"""

import hashlib
import json
import time
from pathlib import Path

import pandas as pd
from sklearn.datasets import load_breast_cancer

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
CHECKSUM_KEY = "vk_fragments.csv"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _sha256_checksum(data: bytes) -> str:
    """Return the hex SHA‑256 checksum of ``data``."""
    sha = hashlib.sha256()
    sha.update(data)
    return sha.hexdigest()

def _load_checksums() -> dict:
    """Load ``data/checksums.json``; return empty dict if missing."""
    checksums_path = paths.data("checksums.json")
    if not checksums_path.is_file():
        log.warning(f"Checksums file not found at {checksums_path}; proceeding with empty set.")
        return {}
    with checksums_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _write_checksums(checksums: dict) -> None:
    """Write the provided checksum mapping to ``data/checksums.json``."""
    checksums_path = paths.data("checksums.json")
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
    log.info(f"Checksums file updated at {checksums_path}")

def _append_provenance(artifact_path: Path, script_name: str) -> None:
    """
    Append a single‑line JSON provenance record to
    ``outputs/logs/ssot_log.jsonl``.
    """
    log_entry = {
        "artifact_path": str(artifact_path),
        "checksum": _sha256_checksum(artifact_path.read_bytes()),
        "generated_by": script_name,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
    }
    ssot_path = paths.outputs("logs", "ssot_log.jsonl")
    ssot_path.parent.mkdir(parents=True, exist_ok=True)
    with ssot_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    log.info(f"Provenance recorded for {artifact_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Generate a small fragment‑contribution CSV using scikit‑learn's breast
    cancer dataset, register its checksum, write it to
    ``data/raw/vk_fragments.csv`` and record provenance.
    """
    # Load or initialise the checksum registry.
    checksums = _load_checksums()

    # Create a simple DataFrame representing fragment contributions.
    cancer = load_breast_cancer()
    df = pd.DataFrame({
        "fragment": cancer.feature_names,
        "contribution": cancer.data.mean(axis=0)
    })
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    # Compute checksum.
    actual_checksum = _sha256_checksum(csv_bytes)

    # Register or verify checksum.
    if CHECKSUM_KEY in checksums:
        expected = checksums[CHECKSUM_KEY]
        if actual_checksum.lower() != expected.lower():
            raise ValueError(
                f"Checksum mismatch for '{CHECKSUM_KEY}': expected {expected}, got {actual_checksum}"
            )
        log.info(f"Checksum verification passed for {CHECKSUM_KEY}")
    else:
        checksums[CHECKSUM_KEY] = actual_checksum
        _write_checksums(checksums)
        log.info(f"Checksum for '{CHECKSUM_KEY}' recorded as {actual_checksum}")

    # Write the CSV to the canonical location.
    vk_path = paths.data("raw", "vk_fragments.csv")
    vk_path.parent.mkdir(parents=True, exist_ok=True)
    vk_path.write_bytes(csv_bytes)
    log.info(f"Van Krevelen fragment table written to {vk_path}")

    # Record provenance.
    _append_provenance(vk_path, Path(__file__).name)

if __name__ == "__main__":
    main()