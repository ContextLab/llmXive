"""
Unit test for the SMILES‑validation logic added in T014.

The test creates a temporary CSV file containing one valid SMILES and one
deliberately invalid SMILES. After running ``ingest`` we assert that:
  * the output JSONL contains only the valid record,
  * the log file includes the ``[ERROR_SMILES]`` tag for the invalid entry.
"""

import csv
import json
import os
from pathlib import Path

import pytest

from ingestion.ingest import ingest
from utils.logging import get_log_file_path

@pytest.fixture
def tmp_csv(tmp_path: Path) -> Path:
    csv_path = tmp_path / "test_dataset.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["smiles", "solvent", "temperature", "viscosity", "dielectric"],
        )
        writer.writeheader()
        # Valid SMILES (methane)
        writer.writerow(
            {
                "smiles": "C",
                "solvent": "water",
                "temperature": "298.15",
                "viscosity": "0.89",
                "dielectric": "78.5",
            }
        )
        # Invalid SMILES
        writer.writerow(
            {
                "smiles": "INVALID_SMILES",
                "solvent": "water",
                "temperature": "298.15",
                "viscosity": "0.89",
                "dielectric": "78.5",
            }
        )
    return csv_path

def test_ingest_skips_invalid_smiles(tmp_path: Path, tmp_csv: Path):
    output_path = tmp_path / "featurized.jsonl"

    # Run ingestion
    ingest(tmp_csv, output_path)

    # Verify only one line was written (the valid SMILES)
    with output_path.open() as f:
        lines = f.readlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["smiles"] == "C"

    # Verify the log contains the [ERROR_SMILES] tag
    log_path = get_log_file_path()
    assert log_path.exists()
    log_contents = log_path.read_text()
    assert "[ERROR_SMILES]" in log_contents
    assert "INVALID_SMILES" in log_contents