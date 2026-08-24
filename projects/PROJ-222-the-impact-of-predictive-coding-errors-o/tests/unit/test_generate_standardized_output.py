import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import yaml

# Import the module under test
from generate_standardized_output import compute_sha256, validate_schema, run_t017
from config import get_data_dir


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


def test_compute_sha256(temp_dir):
    """Test SHA256 checksum computation."""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)

    checksum = compute_sha256(test_file)
    # Known SHA256 for "Hello, World!"
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert checksum == expected


def test_validate_schema_valid(temp_dir):
    """Test schema validation with valid data."""
    schema_path = temp_dir / "schema.yaml"
    schema = {
        "required_columns": ["duration_estimate", "stimulus_sequence", "participant_id"]
    }
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)

    df = pd.DataFrame({
        "duration_estimate": [1.0, 2.0],
        "stimulus_sequence": ["A", "B"],
        "participant_id": [1, 2],
        "extra_col": [3, 4]
    })

    assert validate_schema(df, schema_path) is True


def test_validate_schema_invalid(temp_dir):
    """Test schema validation with missing columns."""
    schema_path = temp_dir / "schema.yaml"
    schema = {
        "required_columns": ["duration_estimate", "stimulus_sequence", "participant_id", "missing_col"]
    }
    with open(schema_path, 'w') as f:
        yaml.dump(schema, f)

    df = pd.DataFrame({
        "duration_estimate": [1.0, 2.0],
        "stimulus_sequence": ["A", "B"],
        "participant_id": [1, 2]
    })

    with pytest.raises(ValueError, match="missing required columns"):
        validate_schema(df, schema_path)


@patch('generate_standard_output.run_preprocessing_pipeline')
@patch('generate_standardized_output.get_data_dir')
@patch('generate_standardized_output.validate_schema')
def test_run_t017_integration(mock_validate, mock_get_dir, mock_preprocess, temp_dir):
    """Test the full T017 pipeline execution."""
    # Setup mocks
    mock_df = pd.DataFrame({
        "duration_estimate": [1.0, 2.0],
        "stimulus_sequence": ["A", "B"],
        "participant_id": [1, 2]
    })
    mock_preprocess.return_value = mock_df
    
    # Mock data directory structure
    processed_dir = temp_dir / "processed"
    processed_dir.mkdir()
    contracts_dir = temp_dir / "contracts"
    contracts_dir.mkdir()
    
    # Create a dummy schema
    schema_path = contracts_dir / "output.schema.yaml"
    with open(schema_path, 'w') as f:
        yaml.dump({"required_columns": ["duration_estimate", "stimulus_sequence", "participant_id"]}, f)

    mock_get_dir.return_value = temp_dir
    mock_validate.return_value = True

    # Run T017
    output_path, checksum = run_t017()

    # Assertions
    assert output_path.exists()
    assert output_path.name == "standardized.csv"
    assert checksum is not None
    assert len(checksum) == 64  # SHA256 hex length

    # Verify checksum file exists
    checksum_path = output_path.parent / "standardized.csv.sha256"
    assert checksum_path.exists()

    # Verify log file exists
    log_path = output_path.parent / "standardized_output.log"
    assert log_path.exists()