import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.summarize_results import load_model_results, extract_summary_statistics, write_summary_statistics

class TestSummarizeResults:
    """
    Tests for the summarize_results module (T028).
    """

    def test_load_model_results(self, tmp_path):
        """Test loading model results from a CSV file."""
        # Create a mock model results CSV
        mock_data = {
            'term': ['rank(burden)', 'sex', 'PC1', 'PC2'],
            'coefficient': [0.5, -0.2, 0.1, 0.05],
            'p_value': [0.01, 0.05, 0.1, 0.2],
            'p_value_adj': [0.02, 0.06, 0.15, 0.25]
        }
        df = pd.DataFrame(mock_data)
        input_path = tmp_path / "model_results.csv"
        df.to_csv(input_path, index=False)

        # Load and verify
        loaded_df = load_model_results(input_path)
        assert len(loaded_df) == 4
        assert 'term' in loaded_df.columns
        assert 'coefficient' in loaded_df.columns

    def test_extract_summary_statistics(self, tmp_path):
        """Test extracting summary statistics for the main effect."""
        # Create a mock model results CSV
        mock_data = {
            'term': ['rank(burden)', 'sex', 'PC1', 'PC2'],
            'coefficient': [0.5, -0.2, 0.1, 0.05],
            'p_value': [0.01, 0.05, 0.1, 0.2],
            'p_value_adj': [0.02, 0.06, 0.15, 0.25]
        }
        df = pd.DataFrame(mock_data)
        input_path = tmp_path / "model_results.csv"
        df.to_csv(input_path, index=False)

        # Load and extract
        loaded_df = load_model_results(input_path)
        summary = extract_summary_statistics(loaded_df)

        # Verify extraction
        assert len(summary) == 1
        assert summary['term'].iloc[0] == 'rank(burden)'
        assert summary['coefficient'].iloc[0] == 0.5
        assert 'p_value_adj' in summary.columns

    def test_write_summary_statistics(self, tmp_path):
        """Test writing summary statistics to a CSV file."""
        # Create a mock summary DataFrame
        summary_df = pd.DataFrame({
            'term': ['rank(burden)'],
            'coefficient': [0.5],
            'p_value': [0.01],
            'p_value_adj': [0.02],
            'analysis_type': ['Rank-OLS'],
            'dependent_variable': ['age'],
            'independent_variable': ['mitochondrial_burden']
        })
        output_path = tmp_path / "analysis_results.csv"

        # Write
        write_summary_statistics(summary_df, output_path)

        # Verify file exists and content
        assert output_path.exists()
        written_df = pd.read_csv(output_path)
        assert len(written_df) == 1
        assert written_df['coefficient'].iloc[0] == 0.5

    def test_extract_summary_statistics_no_burden_term(self, tmp_path):
        """Test extraction when 'burden' term is not found (fallback behavior)."""
        # Create a mock model results CSV without 'burden' in term
        mock_data = {
            'term': ['sex', 'PC1', 'PC2'],
            'coefficient': [-0.2, 0.1, 0.05],
            'p_value': [0.05, 0.1, 0.2],
            'p_value_adj': [0.06, 0.15, 0.25]
        }
        df = pd.DataFrame(mock_data)
        input_path = tmp_path / "model_results.csv"
        df.to_csv(input_path, index=False)

        # Load and extract (should fall back to first row)
        loaded_df = load_model_results(input_path)
        summary = extract_summary_statistics(loaded_df)

        # Verify fallback behavior
        assert len(summary) == 1
        assert summary['term'].iloc[0] == 'sex'  # First row
        assert 'analysis_type' in summary.columns