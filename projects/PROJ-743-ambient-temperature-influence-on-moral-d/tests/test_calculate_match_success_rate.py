"""
Tests for Task T022a: Calculate Match Success Rate
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from calculate_match_success_rate import (
    calculate_success_rate, 
    load_counts, 
    save_success_rate
)

def test_calculate_success_rate_basic():
    """Test basic calculation."""
    counts = {
        'count_total_original_valid_location': 1000,
        'count_matched_pre_exclusion': 800
    }
    rate = calculate_success_rate(counts)
    assert rate == 80.0

def test_calculate_success_rate_zero_total():
    """Test handling of zero total."""
    counts = {
        'count_total_original_valid_location': 0,
        'count_matched_pre_exclusion': 0
    }
    rate = calculate_success_rate(counts)
    assert rate == 0.0

def test_calculate_success_rate_missing_key():
    """Test error handling for missing keys."""
    counts = {
        'count_total_original_valid_location': 1000
        # missing count_matched_pre_exclusion
    }
    with pytest.raises(ValueError):
        calculate_success_rate(counts)

def test_save_and_load_success_rate(tmp_path):
    """Test saving and loading the result file."""
    counts = {
        'count_total_original_valid_location': 500,
        'count_matched_pre_exclusion': 450
    }
    rate = 90.0
    
    output_file = tmp_path / "match_success_rate.json"
    counts_file = tmp_path / "counts.json"
    
    # Write dummy counts file first
    with open(counts_file, 'w') as f:
        json.dump(counts, f)
    
    save_success_rate(rate, str(output_file))
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        result = json.load(f)
    
    assert result['match_success_rate'] == 90.0
    assert result['count_matched_pre_exclusion'] == 450
    assert result['count_total_original_valid_location'] == 500