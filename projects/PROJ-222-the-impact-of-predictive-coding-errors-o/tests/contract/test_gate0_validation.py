import pytest
import pandas as pd
from pathlib import Path
import json
import os

# Import the function to test
from download import validate_gate0, write_gate_status, REQUIRED_COLUMNS

class TestGate0Validation:
    def test_valid_dataset(self):
        """Test that a dataset with all required columns passes Gate 0."""
        df = pd.DataFrame({
            "duration_estimate": [1.0, 2.0],
            "stimulus_sequence": [1, 2],
            "participant_id": ["P1", "P2"],
            "extra_col": [3, 4]
        })
        dataset_info = {"data": df}
        is_valid, reason = validate_gate0(dataset_info)
        assert is_valid is True
        assert "Missing" not in reason

    def test_missing_columns(self):
        """Test that a dataset missing required columns fails Gate 0."""
        df = pd.DataFrame({
            "duration_estimate": [1.0, 2.0],
            # missing stimulus_sequence and participant_id
        })
        dataset_info = {"data": df}
        is_valid, reason = validate_gate0(dataset_info)
        assert is_valid is False
        assert "Missing required columns" in reason

    def test_missing_data(self):
        """Test that None data fails Gate 0."""
        dataset_info = {"data": None}
        is_valid, reason = validate_gate0(dataset_info)
        assert is_valid is False
        assert "No data loaded" in reason

    def test_write_gate_status(self, tmp_path):
        """Test that write_gate_status creates a valid JSON file."""
        status_file = tmp_path / "test_gate.json"
        write_gate_status("blocked", "Test reason", str(status_file))
        
        assert status_file.exists()
        with open(status_file, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "blocked"
        assert data["reason"] == "Test reason"
        assert "timestamp" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
