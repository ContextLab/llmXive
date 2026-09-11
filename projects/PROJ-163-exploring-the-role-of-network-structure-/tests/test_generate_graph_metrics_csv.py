"""
Tests for the generate_graph_metrics_csv module.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import ast

# Import the functions to test
from generate_graph_metrics_csv import load_processed_calibration, compute_device_metrics

def test_load_processed_calibration_valid():
    """Test loading a valid CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test.csv")
        data = {
            'device_id': ['test_device'],
            'coupling_map': ['[(0, 1), (1, 2)]']
        }
        df_input = pd.DataFrame(data)
        df_input.to_csv(csv_path, index=False)
        
        df = load_processed_calibration(csv_path)
        
        assert len(df) == 1
        assert df.iloc[0]['device_id'] == 'test_device'
        assert df.iloc[0]['coupling_map'] == '[(0, 1), (1, 2)]'

def test_load_processed_calibration_missing_file():
    """Test loading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_processed_calibration("non_existent_file.csv")

def test_load_processed_calibration_missing_columns():
    """Test loading a CSV with missing required columns raises ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test.csv")
        data = {
            'device_id': ['test_device'],
            'other_col': ['value']
        }
        df_input = pd.DataFrame(data)
        df_input.to_csv(csv_path, index=False)
        
        with pytest.raises(ValueError):
            load_processed_calibration(csv_path)

def test_compute_device_metrics():
    """Test computing metrics for a simple graph."""
    data = {
        'device_id': ['test_device'],
        'coupling_map': ['[(0, 1), (1, 2)]']
    }
    df = pd.DataFrame(data)
    
    records = compute_device_metrics(df)
    
    assert len(records) > 0
    
    # Check structure of records
    for record in records:
        assert 'device_id' in record
        assert 'metric_name' in record
        assert 'value' in record
        assert 'is_finite' in record
        assert record['device_id'] == 'test_device'
        assert isinstance(record['is_finite'], bool)

def test_compute_device_metrics_disconnected_graph():
    """Test computing metrics for a disconnected graph."""
    # Graph with two disconnected components: 0-1 and 2-3
    data = {
        'device_id': ['disconnected_device'],
        'coupling_map': ['[(0, 1), (2, 3)]']
    }
    df = pd.DataFrame(data)
    
    records = compute_device_metrics(df)
    
    assert len(records) > 0
    
    # Check that spectral gap is 0 for disconnected graph
    spectral_gap_records = [r for r in records if r['metric_name'] == 'spectral_gap']
    if spectral_gap_records:
        assert spectral_gap_records[0]['value'] == 0.0
        assert spectral_gap_records[0]['is_finite'] == True