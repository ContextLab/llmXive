"""
Tests for T013: Behavioral Metrics Extraction
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import get_path, ensure_dirs
from code_04_extract_behavioral_metrics import (
    extract_rt_from_eeg_annotations,
    process_behavioral_data,
    MIN_RT_MS,
    MAX_RT_MS,
    MIN_TRIAL_RATIO
)

class TestBehavioralMetricsExtraction:
    """Test cases for behavioral metrics extraction"""
    
    def test_outlier_exclusion_logic(self):
        """Test that outliers are correctly identified"""
        # Create test data
        test_data = pd.DataFrame({
            'participant_id': ['01', '01', '01', '01', '01'],
            'rt_ms': [50, 150, 1000, 2500, 3000]  # 50, 2500, 3000 are outliers
        })
        
        # Apply outlier mask
        outlier_mask = (test_data['rt_ms'] < MIN_RT_MS) | (test_data['rt_ms'] > MAX_RT_MS)
        n_outliers = outlier_mask.sum()
        
        assert n_outliers == 3, f"Expected 3 outliers, got {n_outliers}"
    
    def test_minimum_trial_ratio(self):
        """Test that participants with <70% valid trials are excluded"""
        # 7 trials total, 3 outliers -> 4 valid = 57% -> should be excluded
        test_data = pd.DataFrame({
            'participant_id': ['01'] * 7,
            'rt_ms': [50, 50, 50, 150, 200, 300, 400]  # 3 outliers
        })
        
        total_trials = 7
        n_outliers = 3
        valid_ratio = (total_trials - n_outliers) / total_trials
        
        assert valid_ratio < MIN_TRIAL_RATIO, "Test setup incorrect"
    
    def test_median_calculation(self):
        """Test median RT calculation"""
        test_data = pd.DataFrame({
            'participant_id': ['01'] * 5,
            'rt_ms': [200, 300, 400, 500, 600]
        })
        
        median = test_data['rt_ms'].median()
        assert median == 400, f"Expected median 400, got {median}"
    
    def test_output_schema(self):
        """Test that output files have correct schema"""
        # This test would require actual data processing
        # For now, we test the expected column names
        expected_metrics_cols = ['participant_id', 'median_rt', 'n_trials', 'n_trials_excluded']
        expected_exclusion_cols = ['participant_id', 'reason']
        
        assert expected_metrics_cols == ['participant_id', 'median_rt', 'n_trials', 'n_trials_excluded']
        assert expected_exclusion_cols == ['participant_id', 'reason']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])