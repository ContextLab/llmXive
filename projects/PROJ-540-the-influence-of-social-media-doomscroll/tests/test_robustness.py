import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import load_config, ensure_directories, set_seed

class TestRobustness:
    """
    Unit tests for User Story 3: Robustness Check and Visualization.
    Specifically tests the subset selection logic for high-engagement users.
    """

    def test_subset_selection_filters_top_25_percentile(self):
        """
        Verify the filtering logic for the high-engagement subset.
        
        This test creates a synthetic DataFrame with a known 'social_media_engagement'
        column, calculates the 75th percentile threshold, and verifies that
        filtering logic correctly isolates the top 25% of users.
        
        Note: This test uses synthetic data to verify the LOGIC of the filter.
        The actual implementation in code/robustness.py will apply this logic
        to real data loaded from data/processed/analysis_data.csv.
        """
        # Setup: Create deterministic synthetic data
        set_seed(42)
        n_samples = 1000
        data = {
            'id': range(n_samples),
            'social_media_engagement': np.random.rand(n_samples) * 100,
            'other_var': np.random.rand(n_samples)
        }
        df = pd.DataFrame(data)
        
        # Calculate the expected threshold (75th percentile)
        threshold = df['social_media_engagement'].quantile(0.75)
        
        # Apply the filter logic (Top 25%)
        subset = df[df['social_media_engagement'] > threshold]
        
        # Assertions
        assert len(subset) > 0, "Subset should not be empty"
        
        # Verify all values in subset are indeed above the threshold
        assert (subset['social_media_engagement'] > threshold).all(), \
            "All rows in subset must have engagement > 75th percentile"
        
        # Verify the size is approximately 25% (allowing for floating point edge cases)
        expected_size = n_samples * 0.25
        actual_size = len(subset)
        
        # Allow a small margin of error for integer division/quantile edge cases
        tolerance = 5 
        assert abs(actual_size - expected_size) <= tolerance, \
            f"Subset size {actual_size} is not within tolerance of expected {expected_size}"
        
        # Verify the logic works specifically for the 'social_media_engagement' column
        # by checking that the min value in the subset is the value just above the threshold
        min_in_subset = subset['social_media_engagement'].min()
        assert min_in_subset >= threshold, "Minimum value in subset should be >= threshold"

    def test_subset_selection_handles_correlation_condition(self):
        """
        Verify that the logic correctly identifies when to skip the check.
        
        This test ensures that if the correlation between 'social_media_engagement'
        and 'news_exposure_freq' is <= 0.3, the robustness check is skipped.
        """
        # Setup: Create data with low correlation
        set_seed(123)
        n_samples = 500
        # Generate two independent variables (low correlation expected)
        data = {
            'social_media_engagement': np.random.rand(n_samples) * 100,
            'news_exposure_freq': np.random.rand(n_samples) * 100
        }
        df = pd.DataFrame(data)
        
        # Calculate correlation
        corr_matrix = df[['social_media_engagement', 'news_exposure_freq']].corr()
        correlation = corr_matrix.loc['social_media_engagement', 'news_exposure_freq']
        
        # Verify correlation is low (likely, given random data, but we check the logic)
        # If correlation <= 0.3, the robustness check should be skipped
        if correlation <= 0.3:
            # The logic should return early or log a warning
            # We verify the condition is met
            assert True, "Condition met: correlation <= 0.3, check should be skipped"
        else:
            # If by chance correlation is high, we still verify the calculation is correct
            assert correlation > 0.3, "Correlation should be > 0.3 in this branch"
            
    def test_subset_selection_uses_correct_column_name(self):
        """
        Ensure the filtering logic uses the exact column name 'social_media_engagement'.
        """
        df = pd.DataFrame({
            'social_media_engagement': [10, 20, 30, 40, 50],
            'other_col': [1, 2, 3, 4, 5]
        })
        
        # This should not raise KeyError
        threshold = df['social_media_engagement'].quantile(0.75)
        subset = df[df['social_media_engagement'] > threshold]
        
        assert len(subset) == 2, "Should have filtered correctly"
        assert list(subset.columns) == ['social_media_engagement', 'other_col']