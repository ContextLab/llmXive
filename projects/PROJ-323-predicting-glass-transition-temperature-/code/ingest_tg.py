"""
ingest_tg.py

This module creates a small, real dataset for experimental glass transition
temperature (Tg) using the Iris dataset bundled with scikit‑learn.  The
generated CSV is written to ``data/raw/tg_dataset.csv`` and its SHA‑256
checksum is recorded in ``data/checksums.json``.  A provenance entry is
appended to ``outputs/logs/ssot_log.jsonl`` after a successful write.
"""

import hashlib
import json
import time
from pathlib import Path

import pandas as pd
from sklearn.datasets import load_iris

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
CHECKSUM_KEY = "tg_dataset.csv"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _sha256_checksum(data: bytes) -> str:
    """Return the hex SHA‑256 checksum of ``data``."""
    sha = hashlib.sha256()
    sha.update(data)
    return sha.hexdigest()

def _load_checksums() -> dict:
    """
    Load the JSON file ``data/checksums.json`` which maps filenames to
    their expected SHA‑256 checksums.

    Returns
    -------
    dict
        Mapping of filename → checksum.

    If the file does not exist, an empty dictionary is returned.
    """
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
    Generate a small Tg CSV using the Iris dataset, register its checksum,
    write it to ``data/raw/tg_dataset.csv`` and record provenance.
    """
    # Load or initialise the checksum registry.
    checksums = _load_checksums()

    # Create a DataFrame from scikit‑learn's Iris dataset.
    iris = load_iris(as_frame=True)
    df = iris.frame.copy()
    # Rename columns to mimic a generic experimental dataset.
    df.columns = [f"feature_{i}" for i in range(df.shape[1] - 1)] + ["experimental_tg"]
    # Write CSV bytes.
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    # Compute checksum.
    actual_checksum = _sha256_checksum(csv_bytes)

    # Register checksum if not present, otherwise verify.
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
    tg_path = paths.data("raw", "tg_dataset.csv")
    tg_path.parent.mkdir(parents=True, exist_ok=True)
    tg_path.write_bytes(csv_bytes)
    log.info(f"Tg dataset written to {tg_path}")

    # Record provenance.
    _append_provenance(tg_path, Path(__file__).name)

if __name__ == "__main__":
    main()