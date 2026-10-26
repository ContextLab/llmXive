"""Unit test for the data extraction script (T003).

This test runs the extraction script and verifies that:
- The output CSV exists.
- It contains at least 500 rows.
- Every row has a non‑empty ``doc_diff`` field.
- The CSV checksum entry exists in ``data/metadata.yaml``.
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib

import yaml

from llmxive_toolkit import paths

def test_commit_pairs_csv():
    csv_path = paths.data("raw", "commit_pairs.csv")
    assert csv_path.exists(), f"{csv_path} does not exist"

    # Verify row count
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) >= 500, f"Expected at least 500 rows, got {len(rows)}"

    # Verify non‑empty doc_diff for each row
    for i, row in enumerate(rows, start=1):
        assert row["doc_diff"].strip(), f"Row {i} has empty doc_diff"

    # Verify checksum recorded in metadata.yaml
    metadata_path = paths.data("metadata.yaml")
    assert metadata_path.is_file(), "metadata.yaml missing"
    with metadata_path.open("r", encoding="utf-8") as f:
        meta = yaml.safe_load(f) or {}
    rel_path = str(csv_path.relative_to(paths.root))
    assert rel_path in meta, f"{rel_path} not listed in metadata.yaml"

    # Compute actual checksum and compare
    sha256 = hashlib.sha256()
    with csv_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual_checksum = sha256.hexdigest()
    recorded_checksum = meta[rel_path]
    assert (
        actual_checksum == recorded_checksum
    ), f"Checksum mismatch for {rel_path}: {actual_checksum} != {recorded_checksum}"