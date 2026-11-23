"""
Unit tests for feature extraction module (T016).
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from features import calculate_lempel_ziv_complexity, calculate_permutation_entropy

def test_lzc_range():
    """Test that LZC values are within expected range [0, 1]."""
    # White noise should have high complexity
    np.random.seed(42)
    white_noise = np.random.randn(1000)
    lzc = calculate_lempel_ziv_complexity(white_noise)
    assert 0.0 <= lzc <= 1.0, f"LZC {lzc} out of range"

    # Constant signal should have low complexity
    const_signal = np.ones(1000)
    lzc_const = calculate_lempel_ziv_complexity(const_signal)
    assert 0.0 <= lzc_const <= 1.0, f"LZC {lzc_const} out of range"

def test_pe_range():
    """Test that Permutation Entropy values are within expected range."""
    np.random.seed(42)
    noise = np.random.randn(1000)
    pe = calculate_permutation_entropy(noise, order=3, delay=1)
    # PE is typically between 0 and log2(6) for order=3, but normalized?
    # nolds.pe returns unnormalized entropy (bits). Max for m=3 is log2(6) ~ 2.58
    assert pe >= 0.0, f"PE {pe} is negative"

def test_csv_columns():
    """Verify the output CSV has the required columns."""
    output_path = "data/analysis/complexity_metrics.csv"
    if not os.path.exists(output_path):
        pytest.skip(f"Output file {output_path} does not exist yet. Run the pipeline first.")
    
    df = pd.read_csv(output_path)
    required_cols = ['participant_id', 'channel', 'segment_id', 'lzc_value', 'pe_value']
    
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"

def test_csv_values_not_nan():
    """Verify that numeric columns contain real values, not all NaN."""
    output_path = "data/analysis/complexity_metrics.csv"
    if not os.path.exists(output_path):
        pytest.skip(f"Output file {output_path} does not exist yet.")
    
    df = pd.read_csv(output_path)
    
    # Check if lzc and pe columns are not entirely NaN
    assert not df['lzc_value'].isna().all(), "All LZC values are NaN"
    assert not df['pe_value'].isna().all(), "All PE values are NaN"

def test_output_exists():
    """Assert the output file exists after pipeline run."""
    output_path = "data/analysis/complexity_metrics.csv"
    assert os.path.exists(output_path), f"Output file {output_path} not found"
