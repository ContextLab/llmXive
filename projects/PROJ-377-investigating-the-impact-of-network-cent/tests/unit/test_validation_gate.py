import os
import sys
import pytest
import pandas as pd
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports if running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.data.validation_gate import validate_metadata_columns

class TestValidateMetadataColumns:
    """Unit tests for the T002 validation gate logic."""

    def test_all_columns_present(self, tmp_path):
        """Test that function returns True when all columns are present."""
        data = {
            "subject_id": [1, 2],
            "pre_motor_score": [10.0, 11.0],
            "post_motor_score": [12.0, 13.0],
            "age": [25, 30],
            "sex": ["M", "F"]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "metadata.csv"
        df.to_csv(csv_path, index=False)

        required = ["pre_motor_score", "post_motor_score", "age", "sex", "subject_id"]
        
        # Should not raise and should return True
        result = validate_metadata_columns(str(csv_path), required)
        assert result is True

    def test_missing_column_exits(self, tmp_path):
        """Test that function exits with error when a required column is missing."""
        data = {
            "subject_id": [1, 2],
            "pre_motor_score": [10.0, 11.0],
            # Missing post_motor_score, age, sex
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "metadata.csv"
        df.to_csv(csv_path, index=False)

        required = ["pre_motor_score", "post_motor_score", "age", "sex", "subject_id"]

        # Mock sys.exit to capture the exit call instead of actually exiting
        with pytest.raises(SystemExit) as excinfo:
            validate_metadata_columns(str(csv_path), required)
        
        assert excinfo.value.code == 1

    def test_file_not_found_exits(self, tmp_path):
        """Test that function exits if the file does not exist."""
        fake_path = str(tmp_path / "nonexistent.csv")
        required = ["pre_motor_score"]

        with pytest.raises(SystemExit) as excinfo:
            validate_metadata_columns(fake_path, required)
        
        assert excinfo.value.code == 1

    def test_empty_file_exits(self, tmp_path):
        """Test that function exits if the file is empty."""
        csv_path = tmp_path / "metadata.csv"
        csv_path.write_text("") # Empty file

        required = ["pre_motor_score"]

        with pytest.raises(SystemExit) as excinfo:
            validate_metadata_columns(str(csv_path), required)
        
        assert excinfo.value.code == 1