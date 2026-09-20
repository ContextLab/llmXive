import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

from code.data.validate_imputed import validate_imputed_data, run_validation

REQUIRED_COLS = [
    "participant_id",
    "pre_self_esteem",
    "post_self_esteem",
    "comparison_tendency",
    "avatar_condition"
]

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def create_valid_csv(path: Path):
    """Create a valid imputed data CSV."""
    data = {
        "participant_id": [f"P{i}" for i in range(10)],
        "pre_self_esteem": [20.0 + i for i in range(10)],
        "post_self_esteem": [21.0 + i for i in range(10)],
        "comparison_tendency": [15.0 + i for i in range(10)],
        "avatar_condition": [0, 1] * 5
    }
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)

def create_missing_col_csv(path: Path):
    """Create a CSV missing a required column."""
    data = {
        "participant_id": [f"P{i}" for i in range(10)],
        "pre_self_esteem": [20.0 + i for i in range(10)],
        "post_self_esteem": [21.0 + i for i in range(10)],
        "comparison_tendency": [15.0 + i for i in range(10)]
    }
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)

def create_nan_csv(path: Path):
    """Create a CSV with NaN values."""
    data = {
        "participant_id": [f"P{i}" for i in range(10)],
        "pre_self_esteem": [20.0 + i for i in range(10)],
        "post_self_esteem": [float('nan') if i == 5 else 21.0 + i for i in range(10)],
        "comparison_tendency": [15.0 + i for i in range(10)],
        "avatar_condition": [0, 1] * 5
    }
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)

def test_validate_imputed_data_valid(temp_dir):
    """Test validation passes on valid data."""
    input_path = temp_dir / "imputed_data.csv"
    output_path = temp_dir / "validation.json"
    create_valid_csv(input_path)

    result = run_validation(input_path, output_path)

    assert result["status"] == "pass"
    assert result["imputation_success"] is True
    assert result["row_count"] == 10

    # Verify file was written
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved = json.load(f)
    assert saved["status"] == "pass"

def test_validate_imputed_data_missing_file(temp_dir):
    """Test validation fails when file is missing."""
    input_path = temp_dir / "nonexistent.csv"
    output_path = temp_dir / "validation.json"

    result = run_validation(input_path, output_path)

    assert result["status"] == "fail"
    assert result["imputation_success"] is False
    assert any("not found" in err for err in result["errors"])

def test_validate_imputed_data_missing_column(temp_dir):
    """Test validation fails when required column is missing."""
    input_path = temp_dir / "imputed_data.csv"
    output_path = temp_dir / "validation.json"
    create_missing_col_csv(input_path)

    result = run_validation(input_path, output_path)

    assert result["status"] == "fail"
    assert result["imputation_success"] is False
    assert any("Missing required columns" in err for err in result["errors"])

def test_validate_imputed_data_nan_values(temp_dir):
    """Test validation fails when NaN values remain."""
    input_path = temp_dir / "imputed_data.csv"
    output_path = temp_dir / "validation.json"
    create_nan_csv(input_path)

    result = run_validation(input_path, output_path)

    assert result["status"] == "fail"
    assert result["imputation_success"] is False
    assert any("Remaining missing values" in err for err in result["errors"])

def test_validate_imputed_data_empty_file(temp_dir):
    """Test validation fails on empty file."""
    input_path = temp_dir / "imputed_data.csv"
    output_path = temp_dir / "validation.json"
    pd.DataFrame(columns=REQUIRED_COLS).to_csv(input_path, index=False)

    result = run_validation(input_path, output_path)

    assert result["status"] == "fail"
    assert result["imputation_success"] is False
    assert any("empty" in err for err in result["errors"])
