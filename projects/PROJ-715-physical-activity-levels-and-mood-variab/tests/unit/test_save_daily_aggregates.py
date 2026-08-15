import pytest
import pandas as pd
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from save_daily_aggregates import save_and_validate
from config import get_path

@pytest.fixture
def mock_schema():
    return {
        "type": "object",
        "required": ["participant_id", "date", "total_steps", "mean_mood", "mood_std", "log_mood_std"],
        "properties": {
            "participant_id": {"type": "string"},
            "date": {"type": "string", "format": "date"},
            "total_steps": {"type": "integer", "minimum": 0},
            "mean_mood": {"type": "number"},
            "mood_std": {"type": "number", "minimum": 0},
            "log_mood_std": {"type": "number"},
            "sleep_duration": {"type": "number", "nullable": True},
            "baseline_affect": {"type": "number", "nullable": True}
        },
        "additionalProperties": False
    }

@pytest.fixture
def valid_dataframe():
    return pd.DataFrame({
        "participant_id": ["P001", "P002"],
        "date": ["2013-03-01", "2013-03-02"],
        "total_steps": [5000, 12000],
        "mean_mood": [3.5, 4.2],
        "mood_std": [0.5, 0.8],
        "log_mood_std": [-0.693, -0.223],
        "sleep_duration": [7.5, 6.2],
        "baseline_affect": [3.0, 3.5]
    })

def test_save_and_validate_success(valid_dataframe, mock_schema, tmp_path):
    """Test that valid data passes validation and is saved."""
    # Mock config to use tmp_path
    with patch('save_daily_aggregates.get_path') as mock_get_path:
        # Setup paths
        output_file = tmp_path / "daily_aggregates.csv"
        schema_file = tmp_path / "schema.yaml"
        
        # Mock get_path to return our tmp paths
        def side_effect(*args):
            if args[0] == "data" and args[1] == "processed" and args[2] == "daily_aggregates.csv":
                return output_file
            elif args[0] == "specs" and args[1] == "001-physical-activity-mood-variability" and args[2] == "contracts" and args[3] == "daily_aggregates.schema.yaml":
                return schema_file
            return tmp_path / "dummy"
        
        mock_get_path.side_effect = side_effect

        # Create dummy schema file
        import yaml
        with open(schema_file, 'w') as f:
            yaml.dump(mock_schema, f)

        # Mock the validation result to be successful
        with patch('save_daily_aggregates.load_schema', return_value=mock_schema):
            with patch('save_daily_aggregates.validate_dataframe', return_value={"valid": True, "errors": []}):
                # Mock pandas read_csv to return our valid dataframe
                with patch('pandas.read_csv', return_value=valid_dataframe):
                    # Mock to_csv to avoid actual file writing issues in test environment if needed,
                    # but we want to ensure the logic runs.
                    with patch.object(pd.DataFrame, 'to_csv') as mock_to_csv:
                        result_path = save_and_validate()
                        
                        assert result_path == output_file
                        mock_to_csv.assert_called_once_with(output_file, index=False)

def test_save_and_validate_fails_invalid_schema(valid_dataframe, tmp_path):
    """Test that invalid data raises an error."""
    with patch('save_daily_aggregates.get_path') as mock_get_path:
        output_file = tmp_path / "daily_aggregates.csv"
        schema_file = tmp_path / "schema.yaml"
        
        def side_effect(*args):
            if args[0] == "data" and args[1] == "processed" and args[2] == "daily_aggregates.csv":
                return output_file
            elif args[0] == "specs" and args[1] == "001-physical-activity-mood-variability" and args[2] == "contracts" and args[3] == "daily_aggregates.schema.yaml":
                return schema_file
            return tmp_path / "dummy"
        
        mock_get_path.side_effect = side_effect

        import yaml
        with open(schema_file, 'w') as f:
            yaml.dump({"type": "object"}, f) # Minimal schema

        # Mock validation to fail
        with patch('save_daily_aggregates.load_schema', return_value={"type": "object"}):
            with patch('save_daily_aggregates.validate_dataframe', return_value={"valid": False, "errors": ["Missing required column"]}):
                with patch('pandas.read_csv', return_value=valid_dataframe):
                    with pytest.raises(ValueError, match="Daily aggregates validation failed"):
                        save_and_validate()

def test_save_and_validate_file_not_found(tmp_path):
    """Test that missing input file raises an error."""
    with patch('save_daily_aggregates.get_path') as mock_get_path:
        output_file = tmp_path / "non_existent.csv"
        schema_file = tmp_path / "schema.yaml"
        
        def side_effect(*args):
            if args[0] == "data" and args[1] == "processed" and args[2] == "daily_aggregates.csv":
                return output_file
            elif args[0] == "specs" and args[1] == "001-physical-activity-mood-variability" and args[2] == "contracts" and args[3] == "daily_aggregates.schema.yaml":
                return schema_file
            return tmp_path / "dummy"
        
        mock_get_path.side_effect = side_effect
        
        # Ensure file doesn't exist
        if output_file.exists():
            output_file.unlink()

        with pytest.raises(FileNotFoundError, match="Preprocessing output not found"):
            save_and_validate()