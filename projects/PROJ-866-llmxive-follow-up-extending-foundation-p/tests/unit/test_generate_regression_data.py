import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from analysis.generate_regression_data import load_processed_logs, save_regression_data_to_csv

def test_load_processed_logs():
    """Test loading a valid JSON log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        log_data = {
            "workflow_id": "test-1",
            "compression_level": 2,
            "token_reduction_pct": 25.5,
            "has_violation": False,
            "is_valid": True
        }
        log_file = tmp_path / "test_log.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f)
        
        logs = load_processed_logs(tmp_path)
        assert len(logs) == 1
        assert logs[0]["workflow_id"] == "test-1"
        assert logs[0]["compression_level"] == 2

def test_load_processed_logs_invalid_json():
    """Test handling of invalid JSON files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        log_file = tmp_path / "invalid.json"
        with open(log_file, 'w') as f:
            f.write("not a json")
        
        # Should not raise, just skip
        logs = load_processed_logs(tmp_path)
        assert len(logs) == 0

def test_save_regression_data_csv():
    """Test generating the CSV with correct aggregation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create sample logs
        logs = [
            {"workflow_id": "1", "compression_level": "2", "token_reduction_pct": 20.0, "has_violation": False, "is_valid": True},
            {"workflow_id": "2", "compression_level": "2", "token_reduction_pct": 22.0, "has_violation": True, "is_valid": True},
            {"workflow_id": "3", "compression_level": "2", "token_reduction_pct": 21.0, "has_violation": False, "is_valid": True},
            {"workflow_id": "4", "compression_level": "5", "token_reduction_pct": 50.0, "has_violation": True, "is_valid": True},
            # Invalid workflow should be skipped
            {"workflow_id": "5", "compression_level": "5", "token_reduction_pct": 51.0, "has_violation": True, "is_valid": False},
        ]
        
        output_file = tmp_path / "tradeoff_curve.csv"
        save_regression_data_to_csv(logs, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            
            # Header + 2 data rows (levels 2 and 5)
            assert len(lines) == 3
            assert "compression_level" in lines[0]
            assert "error_rate" in lines[0]
            
            # Check level 2 row (3 valid samples, 1 violation -> error_rate 0.3333)
            # Mean token red for level 2: (20+22+21)/3 = 21.0
            assert "2" in lines[1]
            assert "0.3333" in lines[1] # 1/3 approx
            
            # Check level 5 row (1 valid sample, 1 violation -> error_rate 1.0)
            # Mean token red for level 5: 50.0
            assert "5" in lines[2]
            assert "1.0" in lines[2]

def test_save_regression_data_empty():
    """Test that empty logs raise an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_file = tmp_path / "empty.csv"
        
        with pytest.raises(ValueError):
            save_regression_data_to_csv([], output_file)
