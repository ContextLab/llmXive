"""Tests for the ingestion module (T001).

The test runs the ingestion entry point (``src.pipeline.ingest.main``) with
default arguments, which triggers a live OpenML search for a corrosion‑related
dataset.  It then verifies that:

* a raw CSV file is written under ``data/raw/``,
* a provenance YAML file exists under ``metadata/dataset.yaml``,
* the SHA‑256 checksum recorded in the provenance file matches the actual
  checksum of the raw file.

The test will fail loudly if no qualifying real dataset can be found,
satisfying the “fail‑loud” requirement.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of *file_path*."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def test_ingest_creates_raw_and_provenance(tmp_path: Path) -> None:
    """
    Run the ingestion script and assert that the expected artifacts are created
    and internally consistent.
    """
    # Import inside the test to avoid side‑effects at import time.
    from src.pipeline.ingest import main as ingest_main

    # Run ingestion with default behaviour (search OpenML).
    exit_code = ingest_main([])
    assert exit_code == 0, "Ingestion script exited with non‑zero code"

    # Locate the raw CSV file written by the ingestion step.
    raw_dir = paths.data("raw")
    raw_files = list(raw_dir.glob("corrosion_*.csv"))
    assert raw_files, f"No raw CSV files found in {raw_dir}"
    raw_path = raw_files[0]

    # Verify that the raw file is a non‑empty CSV.
    assert raw_path.is_file() and raw_path.stat().st_size > 0, (
        f"Raw file {raw_path} is missing or empty"
    )

    # Locate the provenance YAML.
    meta_path = paths.metadata("dataset.yaml")
    assert meta_path.is_file(), f"Provenance file not found at {meta_path}"

    # Load provenance and compare checksums.
    with open(meta_path, "r", encoding="utf-8") as fh:
        provenance = yaml.safe_load(fh)

    recorded_checksum = provenance.get("sha256")
    assert recorded_checksum, "Provenance missing 'sha256' entry"

    actual_checksum = compute_sha256(raw_path)
    assert (
        recorded_checksum == actual_checksum
    ), f"Checksum mismatch: recorded {recorded_checksum}, actual {actual_checksum}"