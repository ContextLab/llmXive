"""
Tests for collinearity detection and handling.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.analyze import check_collinearity

class TestCollinearityDetection:
    def test_high_correlation_detection(self):
        """
        Test that check_collinearity correctly identifies highly correlated features.
        """
        np.random.seed(42)
        # Create data with high correlation
        x1 = np.random.rand(100) * 10
        x2 = x1 * 0.95 + np.random.rand(100) * 0.1 # Highly correlated
        x3 = np.random.rand(100) * 10 # Independent
        
        df = pd.DataFrame({
            'feat1': x1,
            'feat2': x2,
            'feat3': x3
        })
        
        flagged_pairs = check_collinearity(df, threshold=0.8)
        
        assert isinstance(flagged_pairs, list)
        # Should detect (feat1, feat2) as correlated
        found_pair = False
        for pair in flagged_pairs:
            if ('feat1' in pair and 'feat2' in pair) or ('feat2' in pair and 'feat1' in pair):
                found_pair = True
                break
        
        assert found_pair, "Failed to detect highly correlated pair (feat1, feat2)"

    def test_low_correlation_no_detection(self):
        """
        Test that check_collinearity does not flag uncorrelated features.
        """
        np.random.seed(42)
        x1 = np.random.rand(100) * 10
        x2 = np.random.rand(100) * 10
        x3 = np.random.rand(100) * 10
        
        df = pd.DataFrame({
            'feat1': x1,
            'feat2': x2,
            'feat3': x3
        })
        
        flagged_pairs = check_collinearity(df, threshold=0.8)
        
        # Should be empty or very few
        assert len(flagged_pairs) == 0, f"Unexpectedly flagged pairs: {flagged_pairs}"
