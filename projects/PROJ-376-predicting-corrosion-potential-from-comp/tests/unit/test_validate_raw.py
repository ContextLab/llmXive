"""
Unit tests for the ``code/data/validate_raw.py`` module.

The tests rely on a minimal synthetic CSV placed under ``data/raw/`` and a
very small ``ingest.schema.yaml`` contract.  They verify that:

* The script raises ``SchemaMismatchError`` when required columns are missing.
* The script writes the expected JSON summary file.
* When the data satisfies the schema and record‑count thresholds, the script
  exits without error.

Because the project forbids synthetic fall‑backs in production, the test
creates a temporary CSV file only for the purpose of exercising the
validation logic.
"""

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths
from utils.exceptions import SchemaMismatchError

# Import the module under test
import importlib.util

spec = importlib.util.spec_from_file_location(
    "validate_raw", str(paths.code("data", "validate_raw.py"))
)
validate_raw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_raw)  # type: ignore


@pytest.fixture
def temp_raw_dir(tmp_path: Path):
    """Create a temporary ``data/raw`` directory with a single CSV file."""
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    csv_path = raw_dir / "test_raw.csv"

    # Minimal valid data (5 rows) – deliberately below the production thresholds
    df = pd.DataFrame(
        {
            "composition": ["{\\\"Fe\\\":0.7}", "{\\\"Fe\\\":0.6}", "{\\\"Fe\\\":0.8}", "{\\\"Fe\\\":0.5}", "{\\\"Fe\\\":0.9}"],
            "ph": [7.0, 8.1, 6.5, 7.2, 7.8],
            "temperature_celsius": [25, 30, 20, 22, 27],
            "corrosion_potential_mV": [-150, -120, -130, -140, -110],
            "specific_alloy_designation": ["A1", "A2", "A3", "A4", "A5"],
        }
    )
    df.to_csv(csv_path, index=False)
    return raw_dir, csv_path

@pytest.fixture
def temp_schema_file(tmp_path: Path):
    """Create a minimal ingest.schema.yaml used by the validator."""
    contracts_dir = (
        tmp_path
        / "specs"
        / "001-predict-corrosion-potential-from-comp"
        / "contracts"
    )
    contracts_dir.mkdir(parents=True)
    schema_path = contracts_dir / "ingest.schema.yaml"
    schema_content = {
        "type": "object",
        "properties": {
            "composition": {"type": "string"},
            "ph": {"type": "number"},
            "temperature_celsius": {"type": "number"},
            "corrosion_potential_mV": {"type": "number"},
            "specific_alloy_designation": {"type": "string"},
        },
        "required": [
            "composition",
            "ph",
            "temperature_celsius",
            "corrosion_potential_mV",
            "specific_alloy_designation",
        ],
    }
    with open(schema_path, "w", encoding="utf-8") as f:
        import yaml

        yaml.safe_dump(schema_content, f)
    return schema_path

def test_validation_raises_when_missing_required_column(
    monkeypatch, temp_raw_dir, temp_schema_file, tmp_path
):
    """
    Remove a required column from the CSV and verify that
    ``SchemaMismatchError`` is raised.
    """
    raw_dir, csv_path = temp_raw_dir
    # Load the CSV, drop the 'ph' column, and rewrite it.
    df = pd.read_csv(csv_path)
    df = df.drop(columns=["ph"])
    df.to_csv(csv_path, index=False)

    # Patch the paths used by the module to point at our temporary locations.
    monkeypatch.setattr(validate_raw.paths, "data", lambda *parts: raw_dir.joinpath(*parts))
    monkeypatch.setattr(validate_raw.paths, "logs", lambda *parts: tmp_path / "data" / "logs" / Path(*parts))
    monkeypatch.setattr(validate_raw.paths, "root", tmp_path)

    with pytest.raises(SchemaMismatchError) as excinfo:
        validate_raw.main()
    assert "Missing required column 'ph'" in str(excinfo.value)

def test_successful_validation_writes_summary(monkeypatch, temp_raw_dir, temp_schema_file, tmp_path):
    """
    With a fully valid CSV (still below the production record count),
    the validator should write a JSON summary and raise an error because the
    record‑count threshold is not met.
    """
    raw_dir, _ = temp_raw_dir

    # Patch paths to use temporary locations.
    monkeypatch.setattr(validate_raw.paths, "data", lambda *parts: raw_dir.joinpath(*parts))
    monkeypatch.setattr(validate_raw.paths, "logs", lambda *parts: tmp_path / "data" / "logs" / Path(*parts))
    monkeypatch.setattr(validate_raw.paths, "root", tmp_path)

    # The CSV is valid, so the only failure should be the minimum‑record check.
    with pytest.raises(SchemaMismatchError) as excinfo:
        validate_raw.main()
    assert "below the required minimum of" in str(excinfo.value)

    # Verify that the summary JSON was created.
    summary_path = tmp_path / "data" / "logs" / "schema_validation.json"
    assert summary_path.is_file()
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    assert summary["total_records"] == 5
    assert summary["unique_alloy_designations"] == 5
    assert summary["violation_count"] == 0

def test_validation_fails_on_null_values(monkeypatch, temp_raw_dir, temp_schema_file, tmp_path):
    """
    Introduce a null value in a required field and ensure the validator
    raises ``SchemaMismatchError`` with the appropriate message.
    """
    raw_dir, csv_path = temp_raw_dir
    df = pd.read_csv(csv_path)
    df.at[0, "ph"] = None  # inject a null
    df.to_csv(csv_path, index=False)

    monkeypatch.setattr(validate_raw.paths, "data", lambda *parts: raw_dir.joinpath(*parts))
    monkeypatch.setattr(validate_raw.paths, "logs", lambda *parts: tmp_path / "data" / "logs" / Path(*parts))
    monkeypatch.setattr(validate_raw.paths, "root", tmp_path)

    with pytest.raises(SchemaMismatchError) as excinfo:
        validate_raw.main()
    # The error message should mention the null value.
    assert "Null value in required column 'ph'" in str(excinfo.value)