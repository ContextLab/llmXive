"""
Unit test for the validate_metadata script (T002).

The test ensures that the script exits with a non‑zero status when required
columns are missing and succeeds when all columns are present.
"""
import sys
import pandas as pd
import pytest
from pathlib import Path

# Import the functions from the script without executing the script's __main__
from importlib import import_module

validate_module = import_module("code.data.validate_metadata")
verify_columns = getattr(validate_module, "verify_columns")
METADATA_PATH = getattr(validate_module, "METADATA_PATH")

def create_temp_metadata(tmp_path: Path, columns):
    """Utility to write a temporary metadata CSV with the given columns."""
    df = pd.DataFrame(columns=columns)
    # Add a single dummy row to make the CSV non‑empty
    for col in columns:
        df.at[0, col] = 0
    file_path = tmp_path / "metadata.csv"
    df.to_csv(file_path, index=False)
    return file_path

def test_verify_columns_success(tmp_path, caplog):
    # All required columns present
    cols = [
        "pre_motor_score",
        "post_motor_score",
        "age",
        "sex",
        "subject_id",
    ]
    file_path = create_temp_metadata(tmp_path, cols)
    # Patch the module's METADATA_PATH to point to our temp file
    validate_module.METADATA_PATH = Path(file_path)
    df = pd.read_csv(file_path)
    # Should not raise SystemExit
    verify_columns(df)
    # Log should contain success message
    assert any("All required behavioral columns are present" in rec.message for rec in caplog.records)

def test_verify_columns_missing(tmp_path, caplog):
    # Omit one required column
    cols = [
        "pre_motor_score",
        "post_motor_score",
        "age",
        "sex",
        # "subject_id" omitted intentionally
    ]
    file_path = create_temp_metadata(tmp_path, cols)
    validate_module.METADATA_PATH = Path(file_path)
    df = pd.read_csv(file_path)

    with pytest.raises(SystemExit) as excinfo:
        verify_columns(df)
    # Exit code should be 1
    assert excinfo.value.code == 1
    # Log should contain the fatal error message with missing column name
    assert any("Fatal: Dataset lacks behavioral motor task metrics" in rec.message for rec in caplog.records)
    assert any("subject_id" in rec.message for rec in caplog.records)