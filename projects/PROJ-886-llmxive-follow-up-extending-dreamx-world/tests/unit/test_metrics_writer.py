import os
import csv
import tempfile
import pytest
from pathlib import Path

from analysis.metrics_writer import write_metrics_csv, load_metrics_csv, METRICS_COLUMNS

def test_write_and_load_metrics_csv():
    """Test that write_metrics_csv creates a valid file and load_metrics_csv reads it back correctly."""
    test_data = [
        {
            "trajectory_id": "traj_001",
            "model": "dreamx_lite",
            "mae_position": 0.123,
            "mae_rotation": 1.5,
            "convergence": True,
            "sfm_failure_reason": ""
        },
        {
            "trajectory_id": "traj_002",
            "model": "dreamx_lite",
            "mae_position": None,
            "mae_rotation": None,
            "convergence": False,
            "sfm_failure_reason": "insufficient_features"
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_metrics.csv"
        
        # Write
        written_path = write_metrics_csv(test_data, output_path)
        assert Path(written_path).exists()
        
        # Load
        loaded_data = load_metrics_csv(output_path)
        
        # Verify count
        assert len(loaded_data) == len(test_data)
        
        # Verify specific values
        assert loaded_data[0]["trajectory_id"] == "traj_001"
        assert loaded_data[0]["convergence"] is True
        assert abs(loaded_data[0]["mae_position"] - 0.123) < 1e-6
        
        assert loaded_data[1]["trajectory_id"] == "traj_002"
        assert loaded_data[1]["convergence"] is False
        assert loaded_data[1]["mae_position"] is None
        assert loaded_data[1]["sfm_failure_reason"] == "insufficient_features"

def test_write_empty_metrics_csv():
    """Test that writing an empty list creates a file with only headers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "empty_metrics.csv"
        
        write_metrics_csv([], output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == METRICS_COLUMNS
            
            # Verify no data rows
            rows = list(reader)
            assert len(rows) == 0

def test_schema_headers_match():
    """Verify that the defined schema headers match the task requirement."""
    expected_columns = [
        "trajectory_id",
        "model",
        "mae_position",
        "mae_rotation",
        "convergence",
        "sfm_failure_reason"
    ]
    assert METRICS_COLUMNS == expected_columns
