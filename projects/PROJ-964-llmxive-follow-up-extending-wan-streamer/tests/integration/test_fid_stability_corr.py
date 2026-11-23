"""
Integration tests for FID Stability Correlation (T043).

Tests that the calculate_fid_stability_corr module:
1. Correctly loads hybrid output data
2. Calculates FID stability correctly
3. Computes Pearson correlation accurately
4. Updates state.yaml with correct status
5. Handles missing data gracefully
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from metrics.fid_stability_corr import (
    load_hybrid_output,
    calculate_fid_stability,
    calculate_correlation,
    run_fid_stability_correlation,
    CORRELATION_THRESHOLD
)

@pytest.fixture
def temp_hybrid_output():
    """Create a temporary hybrid output file for testing."""
    temp_dir = tempfile.mkdtemp()
    output_path = Path(temp_dir) / 'hybrid_output.parquet'
    
    # Create test data with known correlation
    np.random.seed(42)
    n_samples = 1000
    
    # Create data where delta_magnitude and fid_stability are correlated
    delta_magnitude = np.random.normal(0.5, 0.2, n_samples)
    fid_stability = delta_magnitude * 0.8 + np.random.normal(0, 0.05, n_samples)
    
    df = pd.DataFrame({
        'frame_id': range(n_samples),
        'latency': np.random.normal(10, 2, n_samples),
        'fid_score': np.random.normal(50, 5, n_samples),
        'skip_flag': np.random.choice([True, False], n_samples),
        'delta_magnitude': delta_magnitude
    })
    
    df.to_parquet(output_path)
    
    yield output_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_state_yaml():
    """Create a temporary state.yaml for testing."""
    temp_dir = tempfile.mkdtemp()
    state_path = Path(temp_dir) / 'state.yaml'
    
    # Create empty state file
    state_path.write_text('')
    
    yield state_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_load_hybrid_output_success(temp_hybrid_output):
    """Test successful loading of hybrid output."""
    # Temporarily change the HYBRID_OUTPUT_PATH
    with patch('metrics.fid_stability_corr.HYBRID_OUTPUT_PATH', temp_hybrid_output):
        df = load_hybrid_output()
        
        assert df is not None
        assert len(df) > 0
        assert 'frame_id' in df.columns
        assert 'delta_magnitude' in df.columns

def test_load_hybrid_output_file_not_found():
    """Test handling of missing hybrid output file."""
    with patch('metrics.fid_stability_corr.HYBRID_OUTPUT_PATH', Path('/nonexistent/path.parquet')):
        with pytest.raises(FileNotFoundError):
            load_hybrid_output()

def test_load_hybrid_output_empty():
    """Test handling of empty hybrid output file."""
    temp_dir = tempfile.mkdtemp()
    output_path = Path(temp_dir) / 'empty.parquet'
    
    # Create empty parquet file
    pd.DataFrame().to_parquet(output_path)
    
    try:
        with patch('metrics.fid_stability_corr.HYBRID_OUTPUT_PATH', output_path):
            with pytest.raises(ValueError, match="empty"):
                load_hybrid_output()
    finally:
        shutil.rmtree(temp_dir)

def test_calculate_fid_stability():
    """Test FID stability calculation."""
    df = pd.DataFrame({
        'fid_score': [45, 50, 55, 60],
        'skip_flag': [False, True, True, False]
    })
    
    result_df = calculate_fid_stability(df)
    
    assert 'fid_stability' in result_df.columns
    assert len(result_df) == 4
    
    # Baseline should be average of non-skipped: (45 + 60) / 2 = 52.5
    # Frame 1 (skipped, 50): |50 - 52.5| / 52.5 = 0.0476
    # Frame 2 (skipped, 55): |55 - 52.5| / 52.5 = 0.0476
    expected_stability = [0, 0.0476, 0.0476, 0]
    
    for i, expected in enumerate(expected_stability):
        assert abs(result_df.iloc[i]['fid_stability'] - expected) < 0.001

def test_calculate_correlation(temp_hybrid_output):
    """Test Pearson correlation calculation."""
    with patch('metrics.fid_stability_corr.HYBRID_OUTPUT_PATH', temp_hybrid_output):
        df = load_hybrid_output()
        df = calculate_fid_stability(df)
        
        correlation, p_value = calculate_correlation(df)
        
        assert -1 <= correlation <= 1
        assert 0 <= p_value <= 1

def test_run_fid_stability_correlation_validated(temp_hybrid_output, temp_state_yaml):
    """Test full pipeline when correlation meets threshold."""
    # Create data with high correlation
    np.random.seed(42)
    n_samples = 500
    delta = np.linspace(0, 1, n_samples)
    stability = delta * 0.9 + np.random.normal(0, 0.01, n_samples)
    
    df = pd.DataFrame({
        'frame_id': range(n_samples),
        'latency': np.random.normal(10, 2, n_samples),
        'fid_score': np.random.normal(50, 5, n_samples),
        'skip_flag': np.random.choice([True, False], n_samples),
        'delta_magnitude': delta
    })
    
    df.to_parquet(temp_hybrid_output)
    
    with patch('metrics.fid_stability_corr.HYBRID_OUTPUT_PATH', temp_hybrid_output):
        with patch('metrics.fid_stability_corr.STATE_YAML_PATH', temp_state_yaml):
            with patch('metrics.fid_stability_corr.OUTPUT_METRICS_PATH', 
                     Path(temp_state_yaml.parent) / 'fid_stability_corr.json'):
                
                    result = run_fid_stability_correlation()
                    
                    assert result['status'] == 'validated'
                    assert result['correlation'] >= CORRELATION_THRESHOLD

def test_run_fid_stability_correlation_invalidated(temp_hybrid_output, temp_state_yaml):
    """Test full pipeline when correlation is below threshold."""
    # Create data with low correlation
    np.random.seed(42)
    n_samples = 500
    delta = np.random.normal(0.5, 0.2, n_samples)
    stability = np.random.normal(0.5, 0.2, n_samples)  # Uncorrelated
    
    df = pd.DataFrame({
        'frame_id': range(n_samples),
        'latency': np.random.normal(10, 2, n_samples),
        'fid_score': np.random.normal(50, 5, n_samples),
        'skip_flag': np.random.choice([True, False], n_samples),
        'delta_magnitude': delta
    })
    
    df.to_parquet(temp_hybrid_output)
    
    with patch('metrics.fid_stability_corr.HYBRID_OUTPUT_PATH', temp_hybrid_output):
        with patch('metrics.fid_stability_corr.STATE_YAML_PATH', temp_state_yaml):
            with patch('metrics.fid_stability_corr.OUTPUT_METRICS_PATH', 
                     Path(temp_state_yaml.parent) / 'fid_stability_corr.json'):
                
                    result = run_fid_stability_correlation()
                    
                    assert result['status'] == 'invalidated'
                    assert result['correlation'] < CORRELATION_THRESHOLD

def test_run_fid_stability_correlation_skipped(temp_state_yaml):
    """Test full pipeline when hybrid output is missing."""
    with patch('metrics.fid_stability_corr.HYBRID_OUTPUT_PATH', Path('/nonexistent.parquet')):
        with patch('metrics.fid_stability_corr.STATE_YAML_PATH', temp_state_yaml):
            with patch('metrics.fid_stability_corr.OUTPUT_METRICS_PATH', 
                     Path(temp_state_yaml.parent) / 'fid_stability_corr.json'):
                
                    result = run_fid_stability_correlation()
                    
                    assert result['status'] == 'skipped'
                    assert 'error' in result