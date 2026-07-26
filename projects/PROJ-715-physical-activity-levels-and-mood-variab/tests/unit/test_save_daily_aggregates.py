"""
Unit tests for save_daily_aggregates.py logic.

These tests verify that the script correctly writes the CSV
and that the validation logic works as expected.
"""
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Mock the config to use a temporary directory
import sys
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_paths(tmp_path):
    """Create a temporary directory structure mimicking the project."""
    data_raw = tmp_path / "data" / "raw"
    data_processed = tmp_path / "data" / "processed"
    specs_contracts = tmp_path / "specs" / "001-physical-activity-mood-variability" / "contracts"

    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)
    specs_contracts.mkdir(parents=True)

    # Create a dummy bronze.parquet
    dummy_df = pd.DataFrame({"id": [1], "timestamp": ["2023-01-01"]})
    dummy_df.to_parquet(data_raw / "bronze.parquet")

    # Create a dummy schema
    schema_content = """
    type: object
    properties:
      participant_id:
        type: string
      date:
        type: string
      total_steps:
        type: integer
      mean_mood:
        type: number
      mood_std:
        type: number
    required: [participant_id, date, total_steps, mean_mood, mood_std]
    """
    (specs_contracts / "daily_aggregates.schema.yaml").write_text(schema_content)

    return {
        "tmp_path": tmp_path,
        "data_raw": data_raw,
        "data_processed": data_processed,
        "specs_contracts": specs_contracts,
        "schema_path": specs_contracts / "daily_aggregates.schema.yaml"
    }

def test_save_and_validate(mock_paths):
    """
    Test that the script successfully writes the CSV and validates it
    when the schema is correct.
    """
    from unittest.mock import patch, MagicMock

    # Mock the preprocess function to return a valid DataFrame
    mock_df = pd.DataFrame([
        {"participant_id": "P01", "date": "2023-01-01", "total_steps": 5000, "mean_mood": 3.5, "mood_std": 0.5},
        {"participant_id": "P01", "date": "2023-01-02", "total_steps": 6000, "mean_mood": 4.0, "mood_std": 0.2}
    ])

    # Patch the imports and functions used in save_daily_aggregates
    with patch("code.save_daily_aggregates.get_path") as mock_get_path, \
         patch("code.save_daily_aggregates.preprocess", return_value=mock_df), \
         patch("code.save_daily_aggregates.load_schema") as mock_load_schema, \
         patch("code.save_daily_aggregates.validate_dataframe") as mock_validate:

        # Setup mocks
        mock_get_path.side_effect = lambda x: str(mock_paths["tmp_path"] / x) if x.startswith("data") or x.startswith("specs") else None
        mock_get_path.return_value = str(mock_paths["tmp_path"] / "specs" / "001-physical-activity-mood-variability" / "contracts" / "daily_aggregates.schema.yaml")
        
        # Ensure get_path returns the correct path for the schema specifically
        def path_side_effect(path_str):
            if "daily_aggregates.schema.yaml" in path_str:
                return str(mock_paths["schema_path"])
            if path_str == "data/raw/bronze.parquet":
                return str(mock_paths["data_raw"] / "bronze.parquet")
            if path_str == "data/processed/daily_aggregates.csv":
                return str(mock_paths["data_processed"] / "daily_aggregates.csv")
            return str(mock_paths["tmp_path"] / path_str)

        mock_get_path.side_effect = path_side_effect

        mock_load_schema.return_value = {} # Schema loaded
        mock_validate.return_value = (True, []) # Validation passed

        # Import the main function from the module (re-import to ensure patches apply)
        # We need to reload the module to pick up the patches if it was already imported
        import importlib
        import code.save_daily_aggregates as save_mod
        importlib.reload(save_mod)

        # Run the main function
        save_mod.main()

        # Assertions
        output_csv = mock_paths["data_processed"] / "daily_aggregates.csv"
        assert output_csv.exists(), "Output CSV file was not created."
        
        # Verify content
        result_df = pd.read_csv(output_csv)
        assert len(result_df) == 2
        assert "participant_id" in result_df.columns
        assert "total_steps" in result_df.columns

        # Verify validation was called
        mock_validate.assert_called_once()

def test_validation_fails(mock_paths):
    """
    Test that the script exits with an error when validation fails.
    """
    mock_df = pd.DataFrame([
        {"participant_id": "P01", "date": "2023-01-01", "total_steps": 5000, "mean_mood": 3.5, "mood_std": 0.5}
    ])

    with patch("code.save_daily_aggregates.get_path") as mock_get_path, \
         patch("code.save_daily_aggregates.preprocess", return_value=mock_df), \
         patch("code.save_daily_aggregates.load_schema") as mock_load_schema, \
         patch("code.save_daily_aggregates.validate_dataframe") as mock_validate:

        def path_side_effect(path_str):
            if "daily_aggregates.schema.yaml" in path_str:
                return str(mock_paths["schema_path"])
            if path_str == "data/raw/bronze.parquet":
                return str(mock_paths["data_raw"] / "bronze.parquet")
            if path_str == "data/processed/daily_aggregates.csv":
                return str(mock_paths["data_processed"] / "daily_aggregates.csv")
            return str(mock_paths["tmp_path"] / path_str)

        mock_get_path.side_effect = path_side_effect
        mock_load_schema.return_value = {}
        mock_validate.return_value = (False, ["Missing required column: total_steps"])

        import importlib
        import code.save_daily_aggregates as save_mod
        importlib.reload(save_mod)

        with pytest.raises(SystemExit) as excinfo:
            save_mod.main()

        assert excinfo.value.code == 1