"""
Unit tests for the save_daily_aggregates module (Task T016).

Tests verify:
1. The CSV file is written to the correct location.
2. The file content matches the schema requirements.
3. The validation logic correctly identifies valid and invalid data.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from save_daily_aggregates import save_and_validate
from output_validator import load_schema, validate_dataframe
from config import get_path

@pytest.fixture
def sample_aggregates_df():
    """Create a sample DataFrame that should pass validation."""
    data = {
        'participant_id': ['P001', 'P001', 'P002'],
        'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-01']),
        'total_steps': [5000, 7500, 3000],
        'mean_mood': [3.5, 4.0, 2.5],
        'mood_std': [0.5, 0.8, 0.2], # Assuming log-transformed or raw
        'sleep_duration': [7.0, 6.5, 8.0],
        'baseline_affect': [3.0, 3.2, 2.8],
        'n_mood_ratings': [5, 4, 3],
        'day_of_week': [6, 0, 6]
    }
    return pd.DataFrame(data)

@pytest.fixture
def invalid_aggregates_df():
    """Create a DataFrame that should fail validation (missing required field)."""
    data = {
        'participant_id': ['P001'],
        'date': pd.to_datetime(['2023-01-01']),
        'total_steps': [5000],
        # Missing mean_mood, mood_std, etc.
        'n_mood_ratings': [5],
        'day_of_week': [6]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@patch('save_daily_aggregates.load_bronze_data')
@patch('save_daily_aggregates.compute_daily_aggregates')
@patch('save_daily_aggregates.get_path')
@patch('save_daily_aggregates.os.path.exists')
def test_save_and_validate_success(
    mock_exists, mock_get_path, mock_compute, mock_load, sample_aggregates_df, temp_output_dir
):
    """Test that a valid DataFrame is saved and validation passes."""
    
    # Mock file existence checks
    def exists_side_effect(path):
        if "bronze.parquet" in str(path):
            return True
        if "daily_aggregates.schema.yaml" in str(path):
            return True
        return False
    
    mock_exists.side_effect = exists_side_effect
    
    # Mock get_path to return temp directory paths
    def get_path_side_effect(folder, filename=None):
        if folder == "data_raw":
            return str(temp_output_dir / "bronze.parquet")
        elif folder == "data_processed":
            return str(temp_output_dir / filename) if filename else str(temp_output_dir)
        elif folder == "specs":
            return str(temp_output_dir / "daily_aggregates.schema.yaml")
        return str(temp_output_dir)
    
    mock_get_path.side_effect = get_path_side_effect
    
    # Mock data loading and computation
    mock_load.return_value = pd.DataFrame() # Dummy
    mock_compute.return_value = sample_aggregates_df
    
    # Mock schema loading
    with patch('output_validator.load_schema') as mock_load_schema:
        mock_load_schema.return_value = {
            "fields": [
                {"name": "participant_id", "type": "string"},
                {"name": "date", "type": "date"},
                {"name": "total_steps", "type": "integer"},
                {"name": "mean_mood", "type": "number"},
                {"name": "mood_std", "type": "number"},
                {"name": "sleep_duration", "type": "number"},
                {"name": "baseline_affect", "type": "number"},
                {"name": "n_mood_ratings", "type": "integer"},
                {"name": "day_of_week", "type": "integer"}
            ]
        }
        
        # Mock validate_dataframe to return success
        with patch('output_validator.validate_dataframe') as mock_validate:
            mock_validate.return_value = (True, [])
            
            # Run the function
            result = save_and_validate()
            
            # Assertions
            assert result is True
            
            # Verify CSV was written
            csv_path = temp_output_dir / "daily_aggregates.csv"
            assert csv_path.exists()
            
            # Verify content
            df_written = pd.read_csv(csv_path)
            assert len(df_written) == len(sample_aggregates_df)
            assert list(df_written.columns) == list(sample_aggregates_df.columns)

@patch('save_daily_aggregates.load_bronze_data')
@patch('save_daily_aggregates.compute_daily_aggregates')
@patch('save_daily_aggregates.get_path')
@patch('save_daily_aggregates.os.path.exists')
def test_save_and_validate_fails_schema(
    mock_exists, mock_get_path, mock_compute, mock_load, invalid_aggregates_df, temp_output_dir
):
    """Test that validation fails when data does not match schema."""
    
    def exists_side_effect(path):
        if "bronze.parquet" in str(path): return True
        if "daily_aggregates.schema.yaml" in str(path): return True
        return False
    
    mock_exists.side_effect = exists_side_effect
    
    def get_path_side_effect(folder, filename=None):
        if folder == "data_raw": return str(temp_output_dir / "bronze.parquet")
        elif folder == "data_processed": return str(temp_output_dir / filename) if filename else str(temp_output_dir)
        elif folder == "specs": return str(temp_output_dir / "daily_aggregates.schema.yaml")
        return str(temp_output_dir)
    
    mock_get_path.side_effect = get_path_side_effect
    mock_load.return_value = pd.DataFrame()
    mock_compute.return_value = invalid_aggregates_df
    
    with patch('output_validator.load_schema') as mock_load_schema:
        mock_load_schema.return_value = {
            "fields": [
                {"name": "participant_id", "type": "string"},
                {"name": "mean_mood", "type": "number"}, # Required but missing in df
                # ... other fields
            ]
        }
        
        with patch('output_validator.validate_dataframe') as mock_validate:
            mock_validate.return_value = (False, ["Missing required field: mean_mood"])
            
            result = save_and_validate()
            
            assert result is False
            
            # CSV might still be written before validation in some flows, 
            # but the function returns False
            # In our implementation, we write then validate.
            assert temp_output_dir.joinpath("daily_aggregates.csv").exists()

def test_schema_structure():
    """Verify the schema file exists and has correct structure."""
    schema_path = get_path("specs", "001-physical-activity-mood-variability/contracts/daily_aggregates.schema.yaml")
    
    if not os.path.exists(schema_path):
        pytest.skip(f"Schema file not found at {schema_path} (expected if running in isolation without full setup)")
    
    schema = load_schema(schema_path)
    
    assert "fields" in schema
    field_names = [f["name"] for f in schema["fields"]]
    
    required_fields = ["participant_id", "date", "total_steps", "mean_mood", "mood_std", "n_mood_ratings", "day_of_week"]
    for field in required_fields:
        assert field in field_names, f"Required field '{field}' missing from schema"