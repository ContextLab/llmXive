import pytest
import numpy as np
import pandas as pd
import tempfile
import os
import json

# Import from the project's models module
from models.stratified_analysis import (
    load_processed_data,
    calculate_group_stats,
    assess_variance_heterogeneity,
    run_stratified_analysis
)

def test_calculate_group_stats():
    """Test calculation of group statistics for stratified analysis."""
    # Create sample data
    data = {
        'alloy_type_AlSi10Mg': [1, 1, 1, 0, 0, 0],
        'alloy_type_Inconel625': [0, 0, 0, 1, 1, 1],
        'yield_strength': [300, 320, 310, 450, 470, 460],
        'ductility': [15, 16, 15.5, 25, 24, 24.5]
    }
    df = pd.DataFrame(data)
    
    # Calculate stats for yield_strength by alloy type
    stats = calculate_group_stats(df, target_col='yield_strength', group_col='alloy_type_AlSi10Mg')
    
    assert stats is not None
    assert 'mean' in stats
    assert 'std' in stats
    assert 'count' in stats
    assert 'min' in stats
    assert 'max' in stats

def test_assess_variance_heterogeneity():
    """Test variance heterogeneity assessment."""
    # Create sample data with different variances
    data = {
        'alloy_type_AlSi10Mg': [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
        'yield_strength': [300, 310, 320, 305, 315, 450, 460, 470, 455, 465]
    }
    df = pd.DataFrame(data)
    
    # Assess variance heterogeneity
    result = assess_variance_heterogeneity(df, target_col='yield_strength', group_col='alloy_type_AlSi10Mg')
    
    assert result is not None
    assert 'variance_ratio' in result
    assert 'is_significant' in result

def test_run_stratified_analysis():
    """Test full stratified analysis."""
    # Create sample data
    np.random.seed(42)
    n_samples = 100
    data = {
        'alloy_type_AlSi10Mg': np.random.choice([0, 1], n_samples),
        'alloy_type_Inconel625': np.random.choice([0, 1], n_samples),
        'alloy_type_Ti64': np.random.choice([0, 1], n_samples),
        'yield_strength': np.random.uniform(300, 800, n_samples),
        'ductility': np.random.uniform(10, 30, n_samples)
    }
    df = pd.DataFrame(data)
    
    # Run stratified analysis
    results = run_stratified_analysis(df, target_cols=['yield_strength', 'ductility'])
    
    assert results is not None
    assert 'group_stats' in results
    assert 'variance_heterogeneity' in results

def test_stratified_analysis_with_empty_groups():
    """Test stratified analysis with some empty groups."""
    # Create data where one group is empty
    data = {
        'alloy_type_AlSi10Mg': [1, 1, 1, 1, 1],
        'alloy_type_Inconel625': [0, 0, 0, 0, 0],
        'yield_strength': [300, 320, 310, 305, 315]
    }
    df = pd.DataFrame(data)
    
    # Should handle empty groups gracefully
    results = run_stratified_analysis(df, target_cols=['yield_strength'])
    
    assert results is not None

def test_load_processed_data():
    """Test loading processed data from CSV."""
    # Create sample CSV
    data = {
        'laser_power': [200, 250, 300],
        'scan_speed': [500, 600, 700],
        'alloy_type_AlSi10Mg': [1, 0, 0],
        'alloy_type_Inconel625': [0, 1, 0],
        'yield_strength': [300, 450, 800],
        'ductility': [15, 25, 8]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    loaded_df = load_processed_data(temp_path)
    
    assert loaded_df is not None
    assert len(loaded_df) == 3
    assert 'yield_strength' in loaded_df.columns
    
    os.unlink(temp_path)
