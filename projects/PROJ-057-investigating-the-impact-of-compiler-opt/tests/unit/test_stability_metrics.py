"""
Tests for T023: Aggregation of stability metrics into CSV.
"""
import os
import json
import csv
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the function to test
from code.analysis.stability_metrics_generator import aggregate_stability_metrics

@pytest.fixture
def temp_raw_logs_dir():
    """Create a temporary directory with sample raw log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        # Create a sample raw log file
        log_file = dir_path / "config_O2_matmul.jsonl"
        
        sample_data = [
            {
                "config_id": "O2_matmul",
                "kernel_type": "matmul",
                "output_tensor": np.random.rand(10, 10).astype(np.float32).tolist(),
                "reference_tensor": (np.random.rand(10, 10).astype(np.float32) + 1e-6).tolist(), # Very small error
                "iterations": 1000,
                "median": 0.001
            },
            {
                "config_id": "O3_softmax",
                "kernel_type": "softmax",
                "output_tensor": np.random.rand(5, 5).astype(np.float32).tolist(),
                "reference_tensor": (np.random.rand(5, 5).astype(np.float32) + 1e-4).tolist(), # Larger error
                "iterations": 1000,
                "median": 0.002
            }
        ]
        
        with open(log_file, 'w') as f:
            for entry in sample_data:
                # Convert numpy arrays to lists for JSON serialization if they were numpy
                # In real logs, they might be lists already.
                f.write(json.dumps(entry) + '\n')
        
        yield dir_path

def test_aggregate_stability_metrics_creates_csv(temp_raw_logs_dir):
    """Test that the function creates the CSV with correct columns."""
    output_file = Path(temp_raw_logs_dir.parent) / "test_output.csv"
    
    result_path = aggregate_stability_metrics(temp_raw_logs_dir, output_file)
    
    assert result_path.exists()
    assert result_path == output_file
    
    # Read and verify CSV
    with open(result_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        # Verify headers
        assert 'config_id' in reader.fieldnames
        assert 'kernel_type' in reader.fieldnames
        assert 'l2_error' in reader.fieldnames
        assert 'max_diff' in reader.fieldnames
        assert 'status' in reader.fieldnames
        
        # Verify row count (2 entries)
        assert len(rows) == 2

def test_aggregate_stability_metrics_content(temp_raw_logs_dir):
    """Test that the CSV contains expected data."""
    output_file = Path(temp_raw_logs_dir.parent) / "test_output2.csv"
    
    result_path = aggregate_stability_metrics(temp_raw_logs_dir, output_file)
    
    with open(result_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        # Check that we have rows
        assert len(rows) > 0
        
        # Check that numeric fields are numeric strings
        for row in rows:
            float(row['l2_error']) # Should not raise
            float(row['max_diff']) # Should not raise
            assert row['status'] in ['stable', 'unstable']

def test_aggregate_stability_metrics_empty_dir():
    """Test behavior with an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        output_file = Path(tmpdir) / "empty_output.csv"
        
        result_path = aggregate_stability_metrics(dir_path, output_file)
        
        assert result_path.exists()
        
        with open(result_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0
            
            # Verify headers exist even if empty
            assert 'config_id' in reader.fieldnames
            assert 'kernel_type' in reader.fieldnames
            assert 'l2_error' in reader.fieldnames
            assert 'max_diff' in reader.fieldnames
            assert 'status' in reader.fieldnames