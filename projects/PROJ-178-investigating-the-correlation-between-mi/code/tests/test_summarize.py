"""
Tests for Task T028: Summarize Analysis Results.

Verifies that the summary statistics are correctly extracted and written.
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.summarize_results import extract_summary_statistics, write_summary_statistics, load_model_results

class TestSummarizeResults:
    
    def test_extract_summary_statistics_rank_ols(self):
        """Test extraction of summary stats from a mock Rank-OLS results dataframe."""
        # Create mock data simulating the output of T024/T025
        mock_data = {
            'model_type': ['rank_ols', 'rank_ols', 'rank_ols'],
            'term': ['rank(burden)', 'sex', 'PC1'],
            'coef': [0.45, -0.12, 0.03],
            'p_value': [0.001, 0.15, 0.45],
            'adj_p_value': [0.003, 0.30, 0.60]
        }
        df = pd.DataFrame(mock_data)
        
        summary = extract_summary_statistics(df)
        
        assert len(summary) == 3
        assert 'rank_ols' in summary['model'].values
        assert 'rank(burden)' in summary['term'].values
        
        # Check coefficient for burden
        burden_row = summary[summary['term'] == 'rank(burden)']
        assert len(burden_row) == 1
        assert abs(burden_row.iloc[0]['coefficient'] - 0.45) < 1e-6
        assert abs(burden_row.iloc[0]['p_value'] - 0.001) < 1e-6
        assert abs(burden_row.iloc[0]['adj_p_value'] - 0.003) < 1e-6

    def test_extract_summary_statistics_no_model_type_column(self):
        """Test extraction when model_type column is missing (fallback behavior)."""
        mock_data = {
            'term': ['rank(burden)', 'sex'],
            'coef': [0.50, -0.10],
            'p_value': [0.02, 0.20],
            'adj_p_value': [0.05, 0.40]
        }
        df = pd.DataFrame(mock_data)
        
        # Should not raise an error, should warn and process
        with pytest.warns(None): # Suppress warning for test cleanliness if needed
            summary = extract_summary_statistics(df)
        
        assert len(summary) >= 1
        assert 'rank_ols' in summary['model'].values

    def test_write_summary_statistics(self):
        """Test writing the summary to a temporary CSV file."""
        mock_data = {
            'model': ['rank_ols'],
            'term': ['rank(burden)'],
            'coefficient': [0.45],
            'p_value': [0.001],
            'adj_p_value': [0.003]
        }
        df = pd.DataFrame(mock_data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_analysis_results.csv"
            
            # Mock the ensure_directories to use our temp dir
            with patch('analysis.summarize_results.PROCESSED_DIR', Path(tmpdir)):
                with patch('analysis.summarize_results.SUMMARY_OUTPUT_PATH', output_path):
                    write_summary_statistics(df)
            
            assert output_path.exists()
            
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == 1
            assert loaded_df.iloc[0]['coefficient'] == 0.45

    def test_load_model_results_missing_file(self):
        """Test that load_model_results raises FileNotFoundError if file is missing."""
        with patch('analysis.summarize_results.MODEL_RESULTS_PATH', Path('/nonexistent/path.csv')):
            with pytest.raises(FileNotFoundError):
                load_model_results()