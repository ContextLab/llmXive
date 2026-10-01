import os
import sys
import tempfile
import csv
import pytest
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.schema_validator import (
    validate_csv_schema,
    validate_directory_schema,
    ValidationResult,
    ValidationStatus,
    RAW_SCHEMA_EXPECTED_COLUMNS,
    PROCESSED_SCHEMA_EXPECTED_COLUMNS
)


@pytest.fixture
def temp_raw_dir():
    """Creates a temporary directory with valid and invalid CSV files for raw data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Valid file
        valid_file = tmp_path / "valid_sample.csv"
        with open(valid_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["SampleID", "StressCondition", "Species", "ProteinID", "Abundance"])
            writer.writeheader()
            writer.writerow({"SampleID": "S1", "StressCondition": "Drought", "Species": "Arabidopsis", "ProteinID": "P1", "Abundance": "10.5"})

        # Missing required column
        invalid_file = tmp_path / "missing_col.csv"
        with open(invalid_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["SampleID", "StressCondition", "Species"]) # Missing ProteinID
            writer.writeheader()
            writer.writerow({"SampleID": "S2", "StressCondition": "Heat", "Species": "Rice"})

        # Empty file (header only)
        empty_file = tmp_path / "empty.csv"
        with open(empty_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["SampleID", "StressCondition", "Species", "ProteinID", "Abundance"])
            writer.writeheader()

        yield tmp_path


@pytest.fixture
def temp_processed_dir():
    """Creates a temporary directory with valid processed CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        valid_file = tmp_path / "processed_data.csv"
        with open(valid_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["SampleID", "StressCondition", "Species", "ProteinID", "Abundance", "ImputationMethod"])
            writer.writeheader()
            writer.writerow({"SampleID": "S1", "StressCondition": "Drought", "Species": "Arabidopsis", "ProteinID": "P1", "Abundance": "10.5", "ImputationMethod": "MinProb"})

        yield tmp_path


def test_validate_csv_valid_raw(temp_raw_dir):
    status = validate_csv_schema(temp_raw_dir, "raw")
    # Should have 3 files, 1 valid (the one with data), 2 errors (missing col, empty)
    # Note: The logic counts valid_count only if status is 'valid' or 'warning'.
    # 'missing_col' -> error
    # 'empty' -> error
    # 'valid_sample' -> valid
    assert status.passed is False
    assert status.total_files == 3
    assert len(status.errors) == 2
    assert any("Missing required columns" in err for err in status.errors)
    assert any("fewer than 1 data rows" in err for err in status.errors)


def test_validate_csv_valid_processed(temp_processed_dir):
    status = validate_csv_schema(temp_processed_dir, "processed")
    assert status.passed is True
    assert status.total_files == 1
    assert status.valid_files == 1
    assert len(status.errors) == 0


def test_validate_directory_schema_integration(temp_raw_dir, temp_processed_dir):
    # Create a fake base structure
    with tempfile.TemporaryDirectory() as base_tmp:
        base_path = Path(base_tmp)
        # Create raw dir with content
        raw_dir = base_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        # Copy temp_raw_dir contents to raw_dir
        for f in temp_raw_dir.iterdir():
            (raw_dir / f.name).write_text(f.read_text())

        # Create processed dir with content
        proc_dir = base_path / "data" / "processed"
        proc_dir.mkdir(parents=True)
        # Copy temp_processed_dir contents
        for f in temp_processed_dir.iterdir():
            (proc_dir / f.name).write_text(f.read_text())

        # Run validation
        report = validate_directory_schema(base_path)

        assert "overall_passed" in report
        assert report["overall_passed"] is False # Because raw has errors
        assert "raw_data" in report
        assert "processed_data" in report
        assert report["processed_data"]["passed"] is True


def test_validation_result_structure():
    res = ValidationResult(
        status="valid",
        message="All good",
        details={"key": "value"},
        file_path="test.csv"
    )
    assert res.status == "valid"
    assert res.message == "All good"
    assert res.details["key"] == "value"
    assert res.file_path == "test.csv"
