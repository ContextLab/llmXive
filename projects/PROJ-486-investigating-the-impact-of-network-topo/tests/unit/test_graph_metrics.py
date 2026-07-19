import pytest
import numpy as np
import pandas as pd
import json
import os
import tempfile
from code.graph_metrics import (
    detect_zero_variance_metrics,
    save_metric_flags,
    analyze_and_flag_metrics
)

def test_detect_zero_variance_metrics():
    """Test detection of zero-variance metrics."""
    # Create a DataFrame with one zero-variance metric and one normal metric
    data = {
        'subject_id': ['S1', 'S2', 'S3'],
        'clustering_coefficient': [0.5, 0.5, 0.5],  # Zero variance
        'characteristic_path_length': [2.0, 3.0, 4.0]  # Normal variance
    }
    df = pd.DataFrame(data)
    
    flags = detect_zero_variance_metrics(df)
    
    assert len(flags) == 1
    assert flags[0]['metric_name'] == 'clustering_coefficient'
    assert flags[0]['status'] == 'Non-informative'
    assert 'Zero variance' in flags[0]['reason']

def test_detect_non_zero_variance_metrics():
    """Test that normal variance metrics are not flagged."""
    data = {
        'subject_id': ['S1', 'S2', 'S3'],
        'clustering_coefficient': [0.5, 0.6, 0.7],
        'characteristic_path_length': [2.0, 3.0, 4.0]
    }
    df = pd.DataFrame(data)
    
    flags = detect_zero_variance_metrics(df)
    
    assert len(flags) == 0

def test_save_metric_flags():
    """Test saving flags to JSON."""
    flags = [
        {'metric_name': 'test_metric', 'status': 'Non-informative', 'reason': 'Zero variance'}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        save_metric_flags(flags, temp_path)
        
        with open(temp_path, 'r') as f:
            loaded_flags = json.load(f)
        
        assert loaded_flags == flags
    finally:
        os.unlink(temp_path)

def test_analyze_and_flag_metrics_integration():
    """Test the full pipeline of loading, analyzing, and saving flags."""
    # Create temporary input CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_input = f.name
        f.write('subject_id,clustering_coefficient,characteristic_path_length\n')
        f.write('S1,0.5,2.0\n')
        f.write('S2,0.5,3.0\n')
        f.write('S3,0.5,4.0\n')
    
    # Create temporary output path
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_output = f.name
    
    try:
        flags = analyze_and_flag_metrics(temp_input, temp_output)
        
        assert len(flags) == 1
        assert flags[0]['metric_name'] == 'clustering_coefficient'
        
        # Verify file was written
        assert os.path.exists(temp_output)
        with open(temp_output, 'r') as f:
            loaded_flags = json.load(f)
        assert loaded_flags == flags
    finally:
        os.unlink(temp_input)
        os.unlink(temp_output)

def test_zero_variance_with_nan():
    """Test handling of NaN values in variance calculation."""
    data = {
        'subject_id': ['S1', 'S2', 'S3'],
        'clustering_coefficient': [np.nan, np.nan, np.nan],
        'characteristic_path_length': [2.0, 3.0, 4.0]
    }
    df = pd.DataFrame(data)
    
    flags = detect_zero_variance_metrics(df)
    
    # NaN std should be flagged
    assert len(flags) == 1
    assert flags[0]['metric_name'] == 'clustering_coefficient'
