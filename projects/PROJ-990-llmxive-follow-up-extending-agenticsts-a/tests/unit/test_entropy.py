"""
Unit tests for entropy calculation module.

Tests cover:
- Basic entropy calculation
- Edge cases (NaN, Infinity)
- Empty distributions
- Uniform distributions
"""
import pytest
import numpy as np
import pandas as pd
import json
from pathlib import Path
import sys
import logging
from datetime import datetime
import tempfile
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from entropy import (
    calculate_shannon_entropy,
    extract_move_distribution,
    calculate_entropy_for_trajectory,
    process_trajectories,
    write_warning_log
)

@pytest.fixture
def setup_temp_dirs():
    """Create temporary directories for testing."""
    temp_dir = tempfile.mkdtemp()
    processed_dir = Path(temp_dir) / "data" / "processed"
    processed_dir.mkdir(parents=True)
    yield temp_dir, processed_dir
    # Cleanup would happen here in real tests

def test_calculate_shannon_entropy_uniform_distribution():
    """Test entropy calculation for uniform distribution."""
    # Uniform distribution: 4 outcomes, each with probability 0.25
    probs = np.array([0.25, 0.25, 0.25, 0.25])
    entropy = calculate_shannon_entropy(probs)
    # Expected: log2(4) = 2.0
    assert abs(entropy - 2.0) < 1e-6, f"Expected ~2.0, got {entropy}"

def test_calculate_shannon_entropy_deterministic():
    """Test entropy calculation for deterministic distribution (one outcome)."""
    probs = np.array([1.0, 0.0, 0.0])
    entropy = calculate_shannon_entropy(probs)
    # Expected: 0 (no uncertainty)
    assert entropy == 0.0, f"Expected 0.0, got {entropy}"

def test_calculate_shannon_entropy_empty():
    """Test entropy calculation for empty distribution."""
    probs = np.array([])
    entropy = calculate_shannon_entropy(probs)
    assert np.isnan(entropy), f"Expected NaN for empty distribution, got {entropy}"

def test_calculate_shannon_entropy_invalid_sum():
    """Test entropy calculation with probabilities not summing to 1."""
    # Should normalize internally or handle gracefully
    probs = np.array([0.5, 0.5, 0.5])  # Sum = 1.5
    entropy = calculate_shannon_entropy(probs)
    # Function should handle normalization or return valid entropy
    assert not np.isnan(entropy) and not np.isinf(entropy), f"Unexpected result: {entropy}"

def test_extract_move_distribution_json_string():
    """Test extracting distribution from JSON string."""
    row = pd.Series({
        'move_distribution': '[0.5, 0.3, 0.2]',
        'trajectory_id': 'test-1'
    })
    dist = extract_move_distribution(row)
    expected = np.array([0.5, 0.3, 0.2])
    np.testing.assert_array_almost_equal(dist, expected)

def test_extract_move_distribution_list():
    """Test extracting distribution from list."""
    row = pd.Series({
        'move_distribution': [0.4, 0.4, 0.2],
        'trajectory_id': 'test-2'
    })
    dist = extract_move_distribution(row)
    expected = np.array([0.4, 0.4, 0.2])
    np.testing.assert_array_almost_equal(dist, expected)

def test_extract_move_distribution_empty():
    """Test extracting distribution from empty input."""
    row = pd.Series({
        'move_distribution': [],
        'trajectory_id': 'test-3'
    })
    dist = extract_move_distribution(row)
    assert len(dist) == 0, f"Expected empty array, got {dist}"

def test_extract_move_distribution_no_column():
    """Test extracting distribution when no move_distribution column exists."""
    row = pd.Series({
        'trajectory_id': 'test-4',
        'turn': 1
    })
    dist = extract_move_distribution(row)
    assert len(dist) == 0, f"Expected empty array, got {dist}"

def test_extract_move_distribution_move_counts():
    """Test extracting distribution from move count columns."""
    row = pd.Series({
        'trajectory_id': 'test-5',
        'move_0': 10,
        'move_1': 20,
        'move_2': 30
    })
    dist = extract_move_distribution(row)
    # Expected: [10/60, 20/60, 30/60] = [1/6, 1/3, 1/2]
    expected = np.array([1/6, 1/3, 1/2])
    np.testing.assert_array_almost_equal(dist, expected)

def test_calculate_entropy_for_trajectory_nan_handling():
    """Test that NaN entropy is handled correctly."""
    # Create a row with invalid distribution
    row = pd.Series({
        'move_distribution': [],
        'trajectory_id': 'test-nan',
        'turn': 1
    })
    entropy = calculate_entropy_for_trajectory(row)
    assert np.isnan(entropy), f"Expected NaN for invalid distribution, got {entropy}"

def test_process_trajectories_basic():
    """Test processing a small DataFrame."""
    df = pd.DataFrame([
        {
            'trajectory_id': 't1',
            'turn': 1,
            'move_distribution': [0.5, 0.5]
        },
        {
            'trajectory_id': 't2',
            'turn': 2,
            'move_distribution': [0.25, 0.25, 0.25, 0.25]
        }
    ])
    
    result_df = process_trajectories(df)
    
    assert 'entropy' in result_df.columns
    assert len(result_df) == 2
    # First row: entropy of [0.5, 0.5] = 1.0
    assert abs(result_df.iloc[0]['entropy'] - 1.0) < 1e-6
    # Second row: entropy of uniform 4-outcome = 2.0
    assert abs(result_df.iloc[1]['entropy'] - 2.0) < 1e-6

def test_write_warning_log():
    """Test that warning log is written correctly."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_log_path = f.name
    
    # Temporarily override the warning log path
    import entropy
    original_path = entropy.WARNING_LOG_PATH
    entropy.WARNING_LOG_PATH = Path(temp_log_path)
    
    try:
        test_message = "Test warning message"
        write_warning_log(test_message)
        
        with open(temp_log_path, 'r') as f:
            content = f.read()
        
        assert test_message in content, f"Warning message not found in log: {content}"
        assert 'WARNING' in content, "WARNING level not found in log"
    finally:
        entropy.WARNING_LOG_PATH = original_path
        os.unlink(temp_log_path)

def test_edge_case_nan_logging():
    """Test that NaN entropy cases are logged."""
    df = pd.DataFrame([
        {
            'trajectory_id': 't-nan',
            'turn': 1,
            'move_distribution': []  # Empty distribution leads to NaN
        }
    ])
    
    # Capture log output
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        temp_log_path = f.name
    
    import entropy
    original_path = entropy.WARNING_LOG_PATH
    entropy.WARNING_LOG_PATH = Path(temp_log_path)
    
    try:
        result_df = process_trajectories(df)
        
        with open(temp_log_path, 'r') as f:
            log_content = f.read()
        
        assert 'NaN' in log_content, f"NaN warning not logged: {log_content}"
        assert 't-nan' in log_content, f"Trajectory ID not in log: {log_content}"
    finally:
        entropy.WARNING_LOG_PATH = original_path
        os.unlink(temp_log_path)

def test_entropy_values_range():
    """Test that entropy values are within expected range for valid distributions."""
    # Test various distributions
    test_cases = [
        ([0.5, 0.5], 1.0),  # Max entropy for binary
        ([0.7, 0.3], 0.881),  # Less than max
        ([0.9, 0.1], 0.469),  # Much less
        ([0.33, 0.33, 0.34], 1.585),  # Near max for ternary
    ]
    
    for probs, expected_max in test_cases:
        entropy = calculate_shannon_entropy(np.array(probs))
        # Entropy should be non-negative and <= log2(n)
        n = len(probs)
        max_possible = np.log2(n)
        assert 0 <= entropy <= max_possible + 1e-6, f"Entropy {entropy} out of range [0, {max_possible}] for {probs}"