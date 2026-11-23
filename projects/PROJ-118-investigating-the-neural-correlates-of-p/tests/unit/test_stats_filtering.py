"""
Unit tests for T029: Participant filtering logic in stats.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from code.stats import filter_participants, load_excluded_participants


def test_filter_excluded_participants():
    """Test that participants in the exclusion list are removed."""
    # Create test data
    data = {
        'participant_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
        'peak_detected': [True, True, True, True],
        'standard_amplitude': [1.0, 2.0, 3.0, 4.0],
        'deviant_amplitude': [1.5, 2.5, 3.5, 4.5]
    }
    df = pd.DataFrame(data)
    
    excluded_ids = {'sub-02', 'sub-04'}
    
    filtered = filter_participants(df, excluded_ids)
    
    assert len(filtered) == 2
    assert 'sub-02' not in filtered['participant_id'].values
    assert 'sub-04' not in filtered['participant_id'].values
    assert 'sub-01' in filtered['participant_id'].values
    assert 'sub-03' in filtered['participant_id'].values


def test_filter_peak_detected_false():
    """Test that participants with peak_detected=False are removed."""
    data = {
        'participant_id': ['sub-01', 'sub-02', 'sub-03'],
        'peak_detected': [True, False, True],
        'standard_amplitude': [1.0, 2.0, 3.0],
        'deviant_amplitude': [1.5, 2.5, 3.5]
    }
    df = pd.DataFrame(data)
    
    filtered = filter_participants(df, set())
    
    assert len(filtered) == 2
    assert filtered['peak_detected'].all() == True
    assert 'sub-02' not in filtered['participant_id'].values


def test_filter_combined():
    """Test combined filtering: exclusion list AND peak_detected."""
    data = {
        'participant_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05'],
        'peak_detected': [True, False, True, True, False],
        'standard_amplitude': [1.0, 2.0, 3.0, 4.0, 5.0],
        'deviant_amplitude': [1.5, 2.5, 3.5, 4.5, 5.5]
    }
    df = pd.DataFrame(data)
    
    excluded_ids = {'sub-02', 'sub-04'}
    
    filtered = filter_participants(df, excluded_ids)
    
    # sub-02: excluded by list AND peak=False
    # sub-04: excluded by list (peak=True)
    # sub-05: peak=False
    # Remaining: sub-01, sub-03
    assert len(filtered) == 2
    assert list(filtered['participant_id']) == ['sub-01', 'sub-03']


def test_filter_empty_result():
    """Test that an error is raised when no participants remain."""
    data = {
        'participant_id': ['sub-01'],
        'peak_detected': [False],
        'standard_amplitude': [1.0],
        'deviant_amplitude': [1.5]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="No participants remain after filtering"):
        filter_participants(df, set())


def test_load_excluded_participants(tmp_path):
    """Test loading excluded participants from log file."""
    # Create a mock exclusion log
    log_path = tmp_path / "rejected_participants.log"
    log_content = """# Excluded participants from US1
    sub-01
    sub-05
    # Another comment
    sub-10
    """
    log_path.write_text(log_content)
    
    # Temporarily override the path
    import code.stats
    original_path = code.stats.EXCLUSION_LOG_PATH
    code.stats.EXCLUSION_LOG_PATH = log_path
    
    try:
        excluded = load_excluded_participants()
        assert 'sub-01' in excluded
        assert 'sub-05' in excluded
        assert 'sub-10' in excluded
        assert len(excluded) == 3
    finally:
        code.stats.EXCLUSION_LOG_PATH = original_path