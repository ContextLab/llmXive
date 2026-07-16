import pytest
import pandas as pd
import numpy as np
from regression_analysis import detect_percolation_threshold, update_csv_with_percolation_threshold
import os
import tempfile

def test_percolation_threshold_logic():
    """Test percolation threshold detection: smallest avg_degree where >=80% connected."""
    # Create test data
    data = pd.DataFrame({
        'avg_degree': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        'percolation_flag': [0, 0, 1, 1, 1, 1]  # 0% at deg 1, 0% at deg 2, 100% at deg 3+
    })
    
    # At degree 3, 4, 5, 6 all are connected (100% >= 80%)
    # Threshold should be 3.0
    threshold = detect_percolation_threshold(data)
    
    assert not np.isnan(threshold), "Threshold should be detected"
    assert threshold == 3.0, f"Expected threshold 3.0, got {threshold}"

def test_percolation_threshold_partial_connectivity():
    """Test with partial connectivity at each degree."""
    # Create data with varying connectivity rates
    data = pd.DataFrame({
        'avg_degree': [2.0, 2.0, 2.0, 3.0, 3.0, 3.0, 4.0, 4.0, 4.0],
        'percolation_flag': [0, 0, 1, 0, 1, 1, 1, 1, 1]
    })
    
    # Degree 2: 1/3 = 33.3% connected
    # Degree 3: 2/3 = 66.7% connected
    # Degree 4: 3/3 = 100% connected
    # Threshold should be 4.0 (first degree with >=80%)
    threshold = detect_percolation_threshold(data)
    
    assert not np.isnan(threshold), "Threshold should be detected"
    assert threshold == 4.0, f"Expected threshold 4.0, got {threshold}"

def test_percolation_threshold_no_threshold():
    """Test when no degree reaches 80% connectivity."""
    data = pd.DataFrame({
        'avg_degree': [2.0, 3.0, 4.0],
        'percolation_flag': [0, 0, 1]  # Max 33% at each degree
    })
    
    threshold = detect_percolation_threshold(data)
    
    assert np.isnan(threshold), "Threshold should be NaN when no degree >= 80% connected"

def test_update_csv_with_percolation_threshold():
    """Test updating CSV with percolation threshold."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = f.name
        f.write("seed,N,p,avg_degree,conductivity,percolation_flag\n")
        f.write("1,100,0.1,3.5,10.5,1\n")
    
    try:
        # Update with threshold
        update_csv_with_percolation_threshold(temp_path, 3.0)
        
        # Read back and verify
        df = pd.read_csv(temp_path)
        
        assert 'percolation_threshold' in df.columns, "Column should be added"
        assert df['percolation_threshold'].iloc[0] == 3.0, "Threshold value should be 3.0"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
