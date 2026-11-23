import pytest
import numpy as np
from code.analysis.detect_threshold import detect_threshold, MIN_BIN_SIZE

def test_detect_threshold_no_small_bins():
    """Test that normal detection works when all bins are large enough."""
    # Create data with enough samples in each bin
    chain_lengths = [1] * 100 + [2] * 100 + [3] * 100 + [4] * 100 + [5] * 100
    corrects = [1] * 100 + [1] * 80 + [1] * 60 + [1] * 40 + [1] * 20  # Decreasing accuracy
    
    raw_data = {
        'chain_length': chain_lengths,
        'correctness': corrects
    }
    
    results = detect_threshold(raw_data, min_bin_size=MIN_BIN_SIZE)
    
    assert results['status'] == 'success'
    assert results['bin_status'] == 'none'
    assert 'optimal_knot' in results
    assert 'p_value' in results
    assert results['alpha'] == 0.05
    assert 'is_significant' in results
    assert 'conclusion' in results

def test_detect_threshold_small_bin_merged():
    """Test that small bins are merged correctly."""
    # Create data with a small bin
    chain_lengths = [1] * 100 + [2] * 100 + [3] * 20 + [4] * 100 + [5] * 100
    corrects = [1] * 100 + [1] * 80 + [1] * 15 + [1] * 40 + [1] * 20
    
    raw_data = {
        'chain_length': chain_lengths,
        'correctness': corrects
    }
    
    results = detect_threshold(raw_data, min_bin_size=MIN_BIN_SIZE)
    
    # Should succeed with merged bins
    assert results['status'] == 'success'
    assert results['bin_status'] == 'merged'
    assert 'merged_bin_definition' in results
    assert len(results['merged_bin_definition']) > 0

def test_detect_threshold_deferred():
    """Test that the test is deferred when bins are still too small after merging."""
    # Create data with very small bins that cannot be merged to reach threshold
    chain_lengths = [1] * 100 + [2] * 10 + [3] * 10  # 2 and 3 are very small
    corrects = [1] * 100 + [1] * 5 + [1] * 5
    
    raw_data = {
        'chain_length': chain_lengths,
        'correctness': corrects
    }
    
    results = detect_threshold(raw_data, min_bin_size=MIN_BIN_SIZE)
    
    # Should be deferred
    assert results['status'] == 'deferred'
    assert results['bin_status'] == 'deferred'
    assert results['reason'] == 'insufficient_power'
    assert results['optimal_knot'] is None
    assert results['p_value'] is None
    assert results['conclusion'] is None

def test_detect_threshold_empty_data():
    """Test handling of empty data."""
    raw_data = {
        'chain_length': [],
        'correctness': []
    }
    
    results = detect_threshold(raw_data, min_bin_size=MIN_BIN_SIZE)
    
    assert results['status'] == 'error'
    assert 'reason' in results

def test_detect_threshold_single_bin():
    """Test handling of data with only one bin."""
    chain_lengths = [1] * 100
    corrects = [1] * 80 + [0] * 20
    
    raw_data = {
        'chain_length': chain_lengths,
        'correctness': corrects
    }
    
    results = detect_threshold(raw_data, min_bin_size=MIN_BIN_SIZE)
    
    # With only one bin, there's no change point to detect
    # The function should handle this gracefully
    assert results['status'] == 'success' or results['status'] == 'deferred'