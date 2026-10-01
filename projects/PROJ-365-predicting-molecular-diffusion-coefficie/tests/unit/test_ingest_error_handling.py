"""
Unit test for T014 – ensures that invalid SMILES strings are skipped and
that the appropriate log tag ``[ERROR_SMILES]`` is emitted.

The test creates a temporary CSV with three rows:
1. A valid SMILES (should be processed).
2. An invalid SMILES (should be skipped and logged).
3. A row missing a critical field (should be skipped by the missing‑data guard).

After running ``ingest()``, the output JSONL is inspected for the number of
records, and the log file is examined for the ``[ERROR_SMILES]`` tag.
"""

import csv
import json
import os
from pathlib import Path

import pytest

from ingestion.ingest import ingest, DEFAULT_RAW_CSV, DEFAULT_OUTPUT_JSONL
from utils.logging import get_log_file_path, get_logger

@pytest.fixture
def temp_csv(tmp_path: Path):
    """Create a temporary CSV file with mixed‑validity rows."""
    csv_path = tmp_path / "temp_dataset.csv"
    fieldnames = ["id", "smiles", "solvent", "temperature", "diffusion_coeff"]
    rows = [
        {
            "id": "1",
            "smiles": "CCO",  # valid ethanol
            "solvent": "water",
            "temperature": "298",
            "diffusion_coeff": "0.9",
        },
        {
            "id": "2",
            "smiles": "INVALID_SMILES",
            "solvent": "water",
            "temperature": "298",
            "diffusion_coeff": "1.1",
        },
        {
            "id": "3",
            "smiles": "CCN",  # valid but missing temperature → missing‑data case
            "solvent": "water",
            "temperature": "",
            "diffusion_coeff": "0.8",
        },
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    return csv_path

@pytest.fixture
def temp_output(tmp_path: Path):
    return tmp_path / "out_featurized.jsonl"

def test_invalid_smiles_is_logged_and_skipped(tmp_path, temp_csv, temp_output):
    # Ensure a clean log file for the test
    log_path = get_log_file_path()
    if log_path.exists():
        log_path.unlink()

    # Run the ingestion pipeline on the temporary CSV
    ingest(raw_csv_path=temp_csv, output_jsonl_path=temp_output)

    # --------------------------------------------------------------
    # 1️⃣ Verify output JSONL contains exactly one processed record
    # --------------------------------------------------------------
    with temp_output.open("r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]
    assert len(lines) == 1, "Only the fully valid row should be written"

    # --------------------------------------------------------------
    # 2️⃣ Verify the log contains the [ERROR_SMILES] tag for row 2
    # --------------------------------------------------------------
    assert log_path.exists(), "Log file should have been created"
    log_contents = log_path.read_text(encoding="utf-8")
    assert "[ERROR_SMILES]" in log_contents, "Missing [ERROR_SMILES] tag in log"
    assert "row 2" in log_contents.lower(), "Log should reference the offending row"

# Clean‑up fixture – ensures temporary files are removed after the test
@pytest.fixture(autouse=True)
def cleanup(tmp_path):
    yield
    # Remove any generated files (log, output) within the temporary directory
    log_path = get_log_file_path()
    if log_path.is_file():
        os.remove(log_path)
    # The temporary CSV and output are in ``tmp_path`` and will be auto‑deleted.