"""
Unit tests for the GTEx schema inspection functionality.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Mock the datasets module before importing the module under test
mock_datasets = MagicMock()
mock_dataset_instance = MagicMock()
mock_dataset_instance.features = {
    "bmi": "float64",
    "fasting_glucose": "float64",
    "triglycerides": "float64",
    "hdl": "float64",
    "systolic_bp": "float64",
    "diastolic_bp": "float64",
    "pmi": "int64",
    "time_of_death": "int64",
    "sample_id": "string"
}
mock_datasets.load_dataset.return_value = mock_dataset_instance

with patch.dict("sys.modules", {"datasets": mock_datasets}):
    from data.downloader import inspect_gtex_schema, REQUIRED_COLUMNS


@pytest.fixture
def mock_config(tmp_path):
    """Creates a temporary config.yaml for testing."""
    config_content = """
    datasets:
      gtex:
        source: "mock_gtex_dataset_id"
    random_seed: 42
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_project_paths(tmp_path, mock_config):
    """Sets up the project paths and config for the test."""
    # Create necessary directories
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    
    # Patch get_project_paths to return our temp paths
    with patch("data.downloader.get_project_paths") as mock_paths:
        mock_paths.return_value = {
            "root": str(tmp_path),
            "raw": str(tmp_path / "data" / "raw"),
            "processed": str(tmp_path / "data" / "processed")
        }
        
        # Patch get_config_value to return our temp config path
        with patch("data.downloader.get_config_value") as mock_config_val:
            mock_config_val.return_value = str(mock_config)
            yield tmp_path


def test_inspect_gtex_schema_passes_when_all_columns_present(mock_project_paths):
    """
    Test that inspect_gtex_schema passes and writes 'verified' status 
    when all required columns are present.
    """
    # Ensure the mock returns all required columns
    mock_dataset_instance.features = {col: "string" for col in REQUIRED_COLUMNS}
    mock_dataset_instance.features["extra_col"] = "string"

    result = inspect_gtex_schema()

    assert result["status"] == "verified"
    assert result["missing_columns"] == []
    
    # Verify the output file was written
    output_path = Path(mock_project_paths) / "data" / "processed" / "schema_inspection.json"
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        saved_result = json.load(f)
    
    assert saved_result["status"] == "verified"
    assert saved_result["missing_columns"] == []


def test_inspect_gtex_schema_raises_when_columns_missing(mock_project_paths):
    """
    Test that inspect_gtex_schema raises RuntimeError and writes 'missing_columns' status
    when some required columns are absent.
    """
    # Create a schema missing 'bmi' and 'fasting_glucose'
    available_cols = {col: "string" for col in REQUIRED_COLUMNS}
    del available_cols["bmi"]
    del available_cols["fasting_glucose"]
    mock_dataset_instance.features = available_cols

    # We expect a RuntimeError because the function is designed to halt on missing data
    with pytest.raises(RuntimeError, match="Missing required columns"):
        inspect_gtex_schema()

    # Verify the output file was written with the error status
    output_path = Path(mock_project_paths) / "data" / "processed" / "schema_inspection.json"
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        saved_result = json.load(f)
    
    assert saved_result["status"] == "missing_columns"
    assert "bmi" in saved_result["missing_columns"]
    assert "fasting_glucose" in saved_result["missing_columns"]


def test_inspect_gtex_schema_handles_empty_schema(mock_project_paths):
    """
    Test that inspect_gtex_schema raises RuntimeError when the dataset has no columns.
    """
    mock_dataset_instance.features = {}

    with pytest.raises(RuntimeError, match="Missing required columns"):
        inspect_gtex_schema()