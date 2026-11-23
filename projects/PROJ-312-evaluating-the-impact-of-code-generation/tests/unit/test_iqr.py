import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analyze import calculate_iqr_outliers, verify_outliers

class TestIQR:
    def test_iqr_calculation_basic(self):
        """Test basic IQR calculation and outlier removal."""
        # Create a dataset with known outliers
        data = {
            'turnaround_hours': [1, 2, 3, 4, 5, 100], # 100 is likely an outlier
            'is_ai_assisted': [True, True, True, True, True, True]
        }
        df = pd.DataFrame(data)
        
        cleaned_df, full_df, counts = calculate_iqr_outliers(df)
        
        # Q1=2, Q3=4, IQR=2. Lower=-1, Upper=7. 100 > 7, so it should be removed.
        assert len(cleaned_df) == 5
        assert len(full_df) == 6
        assert counts['AI'] == 1
        assert counts['Non-AI'] == 0

    def test_iqr_calculation_mixed_groups(self):
        """Test IQR calculation with mixed AI and Non-AI groups."""
        data = {
            'turnaround_hours': [1, 2, 3, 100, 1, 2, 3, 200],
            'is_ai_assisted': [True, True, True, True, False, False, False, False]
        }
        df = pd.DataFrame(data)
        
        cleaned_df, full_df, counts = calculate_iqr_outliers(df)
        
        # Both 100 and 200 should be outliers in their respective groups
        assert len(cleaned_df) == 6
        assert counts['AI'] == 1
        assert counts['Non-AI'] == 1

    def test_verify_outliers_pass(self):
        """Test verification function returns True when no outliers exist."""
        data = {
            'turnaround_hours': [1, 2, 3, 4, 5],
            'is_ai_assisted': [True, True, False, False, True]
        }
        df = pd.DataFrame(data)
        
        # Clean data should pass
        assert verify_outliers(df) is True

    def test_verify_outliers_fail(self):
        """Test verification function returns False when outliers exist."""
        data = {
            'turnaround_hours': [1, 2, 3, 1000], # 1000 is an outlier
            'is_ai_assisted': [True, True, True, True]
        }
        df = pd.DataFrame(data)
        
        assert verify_outliers(df) is False

    def test_empty_group_handling(self):
        """Test that empty groups are handled gracefully."""
        data = {
            'turnaround_hours': [1, 2, 3],
            'is_ai_assisted': [True, True, True] # No False values
        }
        df = pd.DataFrame(data)
        
        cleaned_df, full_df, counts = calculate_iqr_outliers(df)
        
        assert len(cleaned_df) == 3
        assert counts['Non-AI'] == 0
        assert counts['AI'] == 0 # No outliers in this small normal set
        assert verify_outliers(cleaned_df) is True
