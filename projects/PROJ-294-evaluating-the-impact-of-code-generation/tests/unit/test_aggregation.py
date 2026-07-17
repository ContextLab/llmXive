import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the function to test
# We need to import from the module, assuming it's in code/
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from analyze_metrics import aggregate_metrics_to_json

def test_aggregate_metrics_to_json():
    """Test that aggregate_metrics_to_json writes a valid JSON file."""
    test_data = [
        {"task_id": "1", "cyclomatic_complexity": 5, "halstead_volume": 10.0, "pass_rate": 1.0, "branch_coverage_pct": 50.0},
        {"task_id": "2", "cyclomatic_complexity": 3, "halstead_volume": 8.0, "pass_rate": 0.0, "branch_coverage_pct": 20.0}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_metrics.json")
        
        aggregate_metrics_to_json(test_data, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_data
        assert len(loaded_data) == 2

def test_aggregate_metrics_empty():
    """Test aggregation with empty list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "empty_metrics.json")
        aggregate_metrics_to_json([], output_path)
        
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == []
