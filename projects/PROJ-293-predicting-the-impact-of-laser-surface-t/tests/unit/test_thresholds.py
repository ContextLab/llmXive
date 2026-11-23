import json
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingest import compare_thresholds, count_records

def test_thresholds_full_study():
    """Test case where normalized_count >= 300"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "counts.json"
        output_path = Path(tmpdir) / "thresholds.json"

        # Write mock counts
        mock_data = {"normalized_count": 350, "raw_count": 50, "total_count": 400}
        with open(input_path, 'w') as f:
            json.dump(mock_data, f)

        # Run function
        result = compare_thresholds(str(input_path), str(output_path))

        assert result["study_scope"] == "full_study"
        assert result["exit_code"] == 0
        assert result["warning"] is None
        assert result["normalized_count"] == 350

        # Verify file written
        with open(output_path, 'r') as f:
            written = json.load(f)
        assert written == result

def test_thresholds_pilot_warning():
    """Test case where 100 <= normalized_count < 300"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "counts.json"
        output_path = Path(tmpdir) / "thresholds.json"

        mock_data = {"normalized_count": 150, "raw_count": 200, "total_count": 350}
        with open(input_path, 'w') as f:
            json.dump(mock_data, f)

        # We expect sys.exit(2), so we catch it
        with pytest.raises(SystemExit) as exc_info:
            compare_thresholds(str(input_path), str(output_path))
        
        assert exc_info.value.code == 2

        # Check file was written before exit
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result["study_scope"] == "pilot_study"
        assert result["exit_code"] == 2
        assert result["warning"] == "data_insufficiency_warning"

def test_thresholds_critical_failure():
    """Test case where normalized_count < 100"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "counts.json"
        output_path = Path(tmpdir) / "thresholds.json"

        mock_data = {"normalized_count": 50, "raw_count": 100, "total_count": 150}
        with open(input_path, 'w') as f:
            json.dump(mock_data, f)

        with pytest.raises(SystemExit) as exc_info:
            compare_thresholds(str(input_path), str(output_path))
        
        assert exc_info.value.code == 1

        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result["study_scope"] == "pilot_study"
        assert result["exit_code"] == 1
        assert result["warning"] == "data_insufficiency_critical"