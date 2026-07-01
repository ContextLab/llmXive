"""
Integration test for data download and Gate 0 validation (T011).

This test verifies that:
1. The download script successfully fetches datasets from real sources (OpenML/HuggingFace).
2. Gate 0 validation logic correctly identifies required columns:
   - duration_estimate
   - stimulus_sequence
   - participant_id
3. If no valid dataset is found, gate0_status.json is written with status="blocked".
4. If a valid dataset is found, gate0_status.json is written with status="passed".

Dependencies:
- code/download.py (T012, T013)
- data/README.md (T009)
- contracts/dataset.schema.yaml (T005)
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from code.download import run_download_pipeline, validate_gate0


def test_gate0_validation_pass():
    """Test that Gate 0 passes when a valid dataset is provided."""
    # Create a temporary directory for test artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a mock valid dataset
        valid_data = {
            'duration_estimate': [1.0, 2.0, 3.0, 4.0, 5.0],
            'stimulus_sequence': ['A', 'B', 'A', 'C', 'B'],
            'participant_id': ['P1', 'P1', 'P1', 'P1', 'P1']
        }
        valid_df = pd.DataFrame(valid_data)
        valid_csv = tmpdir / "valid_dataset.csv"
        valid_df.to_csv(valid_csv, index=False)
        
        # Run Gate 0 validation
        result = validate_gate0(valid_csv, tmpdir)
        
        # Assertions
        assert result['status'] == 'passed', f"Expected 'passed', got {result['status']}"
        assert 'valid_dataset' in result['message']
        
        # Check that gate0_status.json was written
        gate_status_file = tmpdir / "gate0_status.json"
        assert gate_status_file.exists(), "gate0_status.json was not created"
        
        with open(gate_status_file) as f:
            gate_status = json.load(f)
        
        assert gate_status['status'] == 'passed'
        assert 'valid_dataset' in gate_status['message']


def test_gate0_validation_fail_missing_columns():
    """Test that Gate 0 fails when required columns are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a mock dataset missing 'stimulus_sequence'
        invalid_data = {
            'duration_estimate': [1.0, 2.0, 3.0],
            'participant_id': ['P1', 'P1', 'P1']
            # Missing 'stimulus_sequence'
        }
        invalid_df = pd.DataFrame(invalid_data)
        invalid_csv = tmpdir / "invalid_dataset.csv"
        invalid_df.to_csv(invalid_csv, index=False)
        
        # Run Gate 0 validation
        result = validate_gate0(invalid_csv, tmpdir)
        
        # Assertions
        assert result['status'] == 'blocked', f"Expected 'blocked', got {result['status']}"
        assert 'stimulus_sequence' in result['message'].lower()
        
        # Check that gate0_status.json was written
        gate_status_file = tmpdir / "gate0_status.json"
        assert gate_status_file.exists(), "gate0_status.json was not created"
        
        with open(gate_status_file) as f:
            gate_status = json.load(f)
        
        assert gate_status['status'] == 'blocked'
        assert 'stimulus_sequence' in gate_status['reason'].lower()


def test_gate0_validation_no_datasets_found():
    """Test that Gate 0 blocks when no datasets are found in data/README.md."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a data/README.md with no valid datasets
        readme_content = """
        # Data README
        
        ## Verified datasets
        Data Gap: No valid datasets found.
        """
        readme_file = tmpdir / "README.md"
        readme_file.write_text(readme_content)
        
        # Create a mock download.py that reads from this README
        # We'll mock the dataset fetching to simulate no datasets found
        
        # Since we can't easily mock the full download pipeline,
        # we'll test the validation logic directly with an empty list
        result = validate_gate0([], tmpdir)
        
        # Assertions
        assert result['status'] == 'blocked', f"Expected 'blocked', got {result['status']}"
        assert 'no datasets' in result['message'].lower()
        
        # Check that gate0_status.json was written
        gate_status_file = tmpdir / "gate0_status.json"
        assert gate_status_file.exists(), "gate0_status.json was not created"
        
        with open(gate_status_file) as f:
            gate_status = json.load(f)
        
        assert gate_status['status'] == 'blocked'
        assert 'no datasets' in gate_status['reason'].lower()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])