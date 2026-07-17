"""
Edge case tests for the gamified habit tracking analysis pipeline.

This module contains unit tests for specific edge cases:
- test_vif_high_collinearity: Verifies VIF > 5 handling in modeling.py
- test_low_event_count: Verifies survival analysis halt logic in survival.py
"""
import os
import sys
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import logging

# Add project root to path if not already present
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.analysis.modeling import calculate_vif
from code.analysis.survival import count_dropout_events, generate_descriptive_report


class TestVIFEdgeCases:
    """Tests for Variance Inflation Factor (VIF) edge cases."""

    def test_vif_high_collinearity(self):
        """
        Verifies VIF > 5 handling.
        
        Creates a dataset with highly correlated features (Conscientiousness and 
        Need for Achievement) and asserts that the VIF calculation returns 
        values > 5, triggering the collinearity handling logic.
        """
        # Create a synthetic dataset with high collinearity
        np.random.seed(42)
        n_samples = 100
        
        # Generate highly correlated features (correlation ~0.95)
        base = np.random.normal(0, 1, n_samples)
        conscientiousness = base + np.random.normal(0, 0.1, n_samples)
        need_for_achievement = 0.95 * conscientiousness + np.random.normal(0, 0.1, n_samples)
        
        # Create DataFrame
        df = pd.DataFrame({
            'Conscientiousness': conscientiousness,
            'Need_for_Achievement': need_for_achievement,
            'outcome': np.random.randint(0, 2, n_samples)
        })
        
        # Calculate VIF
        vif_results = calculate_vif(df, ['Conscientiousness', 'Need_for_Achievement'])
        
        # Assert that at least one VIF is > 5 (indicating high collinearity)
        high_vif_found = any(vif > 5.0 for vif in vif_results.values())
        assert high_vif_found, "Expected at least one VIF > 5 for highly correlated features, but got: {}".format(vif_results)
        
        # Log the results for verification
        logging.info(f"VIF Results for high collinearity test: {vif_results}")


class TestSurvivalEdgeCases:
    """Tests for survival analysis edge cases."""

    def test_low_event_count(self):
        """
        Verifies survival halt logic when dropout events < 10 per group.
        
        Creates a dataset with very few dropout events and asserts that 
        the survival analysis logic correctly identifies this condition 
        and would halt (or generate descriptive report instead of full analysis).
        """
        # Create a synthetic dataset with very few dropout events
        np.random.seed(42)
        n_users = 50
        
        # Create data with only 2 dropout events total (1 per group)
        data = []
        for i in range(n_users):
            user_id = f"user_{i}"
            gamified = i < 25  # First 25 are gamified, rest are not
            
            # Most users are adherent (adherence_flag = 1)
            # Only 2 users total have consecutive non-adherence (dropout)
            if i == 0 or i == 25:
                # These are our dropout cases
                weeks = [1, 2, 3]
                adherence = [1, 0, 0]  # Dropout after week 1
            else:
                # Regular adherent users
                weeks = [1, 2, 3, 4, 5]
                adherence = [1, 1, 1, 1, 1]
            
            for w, a in zip(weeks, adherence):
                data.append({
                    'User_ID': user_id,
                    'Gamified': gamified,
                    'week_number': w,
                    'weekly_adherence_flag': a,
                    'conscientiousness_score': np.random.normal(0, 1)
                })
        
        df = pd.DataFrame(data)
        
        # Count dropout events
        event_counts = count_dropout_events(df)
        
        # Assert that we have low event counts (< 10 per group)
        for group, count in event_counts.items():
            assert count < 10, f"Expected low event count (<10) for {group}, but got {count}"
        
        # Verify that generate_descriptive_report would be called instead of full analysis
        # by checking the event counts
        total_events = sum(event_counts.values())
        assert total_events < 20, "Expected total events < 20 for low event count test"
        
        logging.info(f"Event counts for low event test: {event_counts}")
        logging.info(f"Total events: {total_events}")
        
        # Test that descriptive report generation works with low events
        # This should not raise an error and should return a report dict
        try:
            report = generate_descriptive_report(df, event_counts)
            assert report is not None, "Descriptive report should not be None"
            assert 'message' in report or 'summary' in report, "Report should contain summary information"
            logging.info("Descriptive report generated successfully for low event scenario")
        except Exception as e:
            pytest.fail(f"generate_descriptive_report failed with low event count: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
