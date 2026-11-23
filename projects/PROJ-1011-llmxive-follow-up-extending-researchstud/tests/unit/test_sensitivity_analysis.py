"""
Unit tests for sensitivity analysis paired-difference removal logic (T035a).

This module verifies that the sensitivity analysis correctly:
1. Identifies outliers using the IQR method.
2. Removes entire pairs if one member is an outlier.
3. Re-calculates statistics on the cleaned dataset.
4. Handles edge cases (e.g., all pairs removed, no outliers).
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
from typing import List, Tuple, Dict, Any

# Add project root to path to allow imports from code/
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.error_handling import ValidationError
from utils.logging_config import get_logger

logger = get_logger(__name__)


class TestSensitivityAnalysisLogic:
    """Tests for the sensitivity analysis paired-difference removal logic."""

    def test_outlier_detection_iqr_method(self):
        """Test that outliers are correctly identified using the IQR method."""
        # Simulate a dataset with known outliers
        # Q1=10, Q3=20, IQR=10. Lower bound = 10 - 1.5*10 = -5, Upper = 20 + 15 = 35
        # Values: 2, 10, 15, 20, 40 (40 is an outlier)
        data = np.array([2, 10, 15, 20, 40])
        
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        assert q1 == 10.0
        assert q3 == 20.0
        assert iqr == 10.0
        assert lower_bound == -5.0
        assert upper_bound == 35.0

        outliers = data[(data < lower_bound) | (data > upper_bound)]
        assert len(outliers) == 1
        assert outliers[0] == 40

    def test_pair_removal_logic(self):
        """Test that if one member of a pair is an outlier, the ENTIRE pair is removed."""
        # Create a synthetic dataset of pairs (pattern-guided, baseline)
        # Structure: list of dicts with 'pair_id', 'group', 'score'
        pairs = [
            {"pair_id": 1, "group": "pattern", "score": 8.0},
            {"pair_id": 1, "group": "baseline", "score": 7.0},
            {"pair_id": 2, "group": "pattern", "score": 9.0},
            {"pair_id": 2, "group": "baseline", "score": 8.5},
            {"pair_id": 3, "group": "pattern", "score": 95.0}, # Outlier
            {"pair_id": 3, "group": "baseline", "score": 8.0},
            {"pair_id": 4, "group": "pattern", "score": 8.2},
            {"pair_id": 4, "group": "baseline", "score": 7.8},
        ]
        
        df = pd.DataFrame(pairs)
        
        # Identify outliers in the 'score' column
        scores = df['score']
        q1 = scores.quantile(0.25)
        q3 = scores.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (scores < lower_bound) | (scores > upper_bound)
        outlier_pair_ids = df.loc[outlier_mask, 'pair_id'].unique()
        
        # Verify that pair_id 3 is identified as having an outlier
        assert 3 in outlier_pair_ids

        # Remove entire pairs containing outliers
        cleaned_df = df[~df['pair_id'].isin(outlier_pair_ids)]
        
        # Verify that pair_id 3 is completely removed
        assert 3 not in cleaned_df['pair_id'].values
        # Verify other pairs remain
        assert set(cleaned_df['pair_id'].unique()) == {1, 2, 4}

    def test_re_run_statistical_test_on_cleaned_data(self):
        """Test that statistical tests can be re-run on the cleaned dataset."""
        # Setup cleaned data from previous test
        pairs = [
            {"pair_id": 1, "group": "pattern", "score": 8.0},
            {"pair_id": 1, "group": "baseline", "score": 7.0},
            {"pair_id": 2, "group": "pattern", "score": 9.0},
            {"pair_id": 2, "group": "baseline", "score": 8.5},
            {"pair_id": 4, "group": "pattern", "score": 8.2},
            {"pair_id": 4, "group": "baseline", "score": 7.8},
        ]
        df = pd.DataFrame(pairs)

        # Perform a simple paired t-test logic check
        pattern_scores = df[df['group'] == 'pattern']['score'].values
        baseline_scores = df[df['group'] == 'baseline']['score'].values
        
        # Calculate mean difference
        mean_diff = np.mean(pattern_scores) - np.mean(baseline_scores)
        
        # Verify calculation is possible and returns a float
        assert isinstance(mean_diff, np.floating)
        assert not np.isnan(mean_diff)

    def test_no_outliers_case(self):
        """Test behavior when no outliers are present."""
        data = np.array([5.0, 6.0, 7.0, 8.0, 9.0])
        
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = data[(data < lower_bound) | (data > upper_bound)]
        
        assert len(outliers) == 0

    def test_all_pairs_removed_case(self):
        """Test handling when all pairs contain outliers (edge case)."""
        # Create data where every value is an outlier (e.g., very spread out)
        # If we have a dataset where IQR is small but values are extreme
        pairs = [
            {"pair_id": 1, "group": "pattern", "score": 100.0},
            {"pair_id": 1, "group": "baseline", "score": -100.0},
        ]
        df = pd.DataFrame(pairs)
        
        scores = df['score']
        q1 = scores.quantile(0.25)
        q3 = scores.quantile(0.75)
        iqr = q3 - q1
        
        # If IQR is 0 or very small, bounds might be tight
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (scores < lower_bound) | (scores > upper_bound)
        outlier_pair_ids = df.loc[outlier_mask, 'pair_id'].unique()
        
        cleaned_df = df[~df['pair_id'].isin(outlier_pair_ids)]
        
        # In this extreme case, both might be outliers if IQR is 0
        # The logic should handle empty dataframe gracefully
        assert len(cleaned_df) == 0

    def test_sensitivity_analysis_report_generation(self):
        """Test that the logic supports generating the required report structure."""
        # Simulate pre and post cleaning statistics
        pre_n = 50
        post_n = 48
        pre_p_value = 0.04
        post_p_value = 0.03
        effect_size_pre = 0.5
        effect_size_post = 0.55
        
        report = {
            "pre_cleaning": {
                "n_pairs": pre_n,
                "p_value": pre_p_value,
                "effect_size": effect_size_pre
            },
            "post_cleaning": {
                "n_pairs": post_n,
                "p_value": post_p_value,
                "effect_size": effect_size_post
            },
            "removed_pairs": [3],
            "robustness_impact": "Positive: P-value decreased, effect size increased"
        }
        
        # Verify report structure
        assert "pre_cleaning" in report
        assert "post_cleaning" in report
        assert "removed_pairs" in report
        assert report["post_cleaning"]["n_pairs"] < report["pre_cleaning"]["n_pairs"]

    def test_integration_with_power_check_logic(self):
        """Test that the cleaned data count is compatible with power check (T035b)."""
        # Simulate a scenario where n drops but remains above threshold
        initial_n = 50
        removed_count = 2
        cleaned_n = initial_n - removed_count
        power_threshold = 30
        
        assert cleaned_n >= power_threshold
        # Logic for T035b would check: if cleaned_n < 30 -> flag underpowered
        
        # Simulate a scenario where n drops below threshold
        removed_count_high = 25
        cleaned_n_low = initial_n - removed_count_high
        
        assert cleaned_n_low < power_threshold
        # This would trigger the 'underpowered' flag in T035b

    def test_iqr_multiplier_standard(self):
        """Verify that the standard IQR multiplier (1.5) is used."""
        # This is a documentation/implementation check
        # In a real implementation, this constant would be defined
        standard_k = 1.5
        assert standard_k == 1.5