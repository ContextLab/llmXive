"""
Unit tests for T043: Tractography-Function Correlation Sensitivity.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.tractography_correlation_sensitivity import (
    load_structural_metrics_by_threshold,
    load_dynamic_metrics,
    run_correlation_for_threshold,
    main
)

@pytest.fixture
def mock_structural_data():
    """Mock structural data with multiple thresholds."""
    data = {
        'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-01', 'sub-02', 'sub-03'],
        'confidence_threshold': [0.0, 0.0, 0.0, 0.4, 0.4, 0.4],
        'global_efficiency': [0.5, 0.6, 0.55, 0.45, 0.55, 0.5],
        'clustering': [0.3, 0.4, 0.35, 0.25, 0.35, 0.3],
        'modularity': [0.4, 0.45, 0.42, 0.38, 0.43, 0.41]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_dynamic_data():
    """Mock dynamic data."""
    data = {
        'subject_id': ['sub-01', 'sub-02', 'sub-03'],
        'mean_dwell_time': [10.0, 12.0, 11.0],
        'num_visits': [5.0, 6.0, 5.5]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_input_files(tmp_path, mock_structural_data, mock_dynamic_data):
    """Create temporary input files for testing."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    struct_path = processed_dir / "tractography_sensitivity_metrics.csv"
    mock_structural_data.to_csv(struct_path, index=False)
    
    dyn_path = processed_dir / "dynamic_metrics.csv"
    mock_dynamic_data.to_csv(dyn_path, index=False)
    
    return tmp_path

def test_load_structural_metrics_by_threshold(temp_input_files, mock_structural_data):
    """Test loading structural metrics from CSV."""
    with patch('analysis.tractography_correlation_sensitivity.project_root', temp_input_files):
        df = load_structural_metrics_by_threshold([0.0, 0.4])
        assert len(df) == 6
        assert 'confidence_threshold' in df.columns
        assert 0.0 in df['confidence_threshold'].values
        assert 0.4 in df['confidence_threshold'].values

def test_load_dynamic_metrics(temp_input_files, mock_dynamic_data):
    """Test loading and aggregating dynamic metrics."""
    with patch('analysis.tractography_correlation_sensitivity.project_root', temp_input_files):
        df = load_dynamic_metrics()
        assert len(df) == 3
        assert 'mean_dwell_time' in df.columns
        assert 'num_visits' in df.columns

def test_run_correlation_for_threshold(temp_input_files, mock_structural_data, mock_dynamic_data):
    """Test correlation calculation for a single threshold."""
    with patch('analysis.tractography_correlation_sensitivity.project_root', temp_input_files):
        struct_df = load_structural_metrics_by_threshold([0.0])
        dyn_df = load_dynamic_metrics()
        
        result = run_correlation_for_threshold(struct_df, dyn_df, 0.0)
        
        assert isinstance(result, pd.DataFrame)
        assert 'metric_pair' in result.columns
        assert 'correlation_r' in result.columns
        assert 'p_value_fdr' in result.columns
        assert 'significant' in result.columns
        assert len(result) > 0  # Should have multiple metric pairs

def test_run_correlation_for_threshold_insufficient_data(temp_input_files):
    """Test handling of insufficient data."""
    # Create a dataset with only 2 subjects
    data = {
        'subject_id': ['sub-01', 'sub-02'],
        'confidence_threshold': [0.0, 0.0],
        'global_efficiency': [0.5, 0.6],
        'clustering': [0.3, 0.4],
        'modularity': [0.4, 0.45]
    }
    struct_df = pd.DataFrame(data)
    dyn_df = pd.DataFrame({
        'subject_id': ['sub-01', 'sub-02'],
        'mean_dwell_time': [10.0, 12.0],
        'num_visits': [5.0, 6.0]
    })
    
    with patch('analysis.tractography_correlation_sensitivity.project_root', temp_input_files):
        # This should raise ValueError because n < 3
        with pytest.raises(ValueError, match="Insufficient subjects"):
            run_correlation_for_threshold(struct_df, dyn_df, 0.0)

def test_fdr_correction_applied(temp_input_files, mock_structural_data, mock_dynamic_data):
    """Test that FDR correction is applied to p-values."""
    with patch('analysis.tractography_correlation_sensitivity.project_root', temp_input_files):
        struct_df = load_structural_metrics_by_threshold([0.0])
        dyn_df = load_dynamic_metrics()
        
        result = run_correlation_for_threshold(struct_df, dyn_df, 0.0)
        
        # Check that FDR p-values are different from raw (or at least present)
        assert 'p_value_raw' in result.columns
        assert 'p_value_fdr' in result.columns
        # FDR values should be <= 1.0
        assert all(result['p_value_fdr'] <= 1.0)
