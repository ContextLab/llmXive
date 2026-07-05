import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analyze import run_sensitivity_analysis, clean_data

class TestSensitivityAnalysis:
    @pytest.fixture
    def mock_df(self):
        """Create a mock dataframe for testing."""
        data = {
            'llm_adoption_flag': [1, 0, 1, 0, 1, 0],
            'iteration_count': [5, 2, 8, 1, 12, 3],
            'avg_comment_length': [10.0, 5.0, 12.0, 4.0, 15.0, 6.0],
            'review_thread_depth': [2, 1, 3, 1, 4, 1],
            'domain_complexity': [1, 1, 2, 1, 2, 1],
            'repository_id': ['A', 'A', 'B', 'B', 'C', 'C']
        }
        return pd.DataFrame(data)

    def test_run_sensitivity_analysis_basic(self, mock_df):
        """Test that sensitivity analysis runs and returns expected structure."""
        thresholds = [1, 3, 5]
        results = run_sensitivity_analysis(mock_df, thresholds)
        
        assert isinstance(results, list)
        assert len(results) == len(thresholds)
        
        for res in results:
            assert 'threshold' in res
            assert 'n_rows' in res
            assert 'coef' in res
            assert 'pvalue' in res
            assert 'status' in res

    def test_sensitivity_analysis_empty_filter(self, mock_df):
        """Test behavior when threshold filters out all data."""
        # Iteration counts in mock are max 12. Set threshold > 12
        thresholds = [100]
        results = run_sensitivity_analysis(mock_df, thresholds)
        
        assert results[0]['status'] == 'empty_dataset'
        assert results[0]['n_rows'] == 0
        assert results[0]['coef'] is None

    def test_sensitivity_analysis_threshold_logic(self, mock_df):
        """Verify that higher thresholds reduce n_rows correctly."""
        thresholds = [1, 5, 10]
        results = run_sensitivity_analysis(mock_df, thresholds)
        
        n_rows = [r['n_rows'] for r in results]
        # n_rows should be non-increasing as threshold increases
        assert n_rows[0] >= n_rows[1] >= n_rows[2]
        
        # Specific check: threshold 1 should include all (min is 1)
        assert n_rows[0] == len(mock_df)
        
        # Threshold 10 should only include 12 (one row)
        # Data: 5, 2, 8, 1, 12, 3 -> only 12 >= 10
        assert n_rows[2] == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])