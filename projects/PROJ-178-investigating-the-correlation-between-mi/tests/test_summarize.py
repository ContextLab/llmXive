import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.summarize_results import load_model_results, extract_summary_statistics, write_summary_statistics

class TestSummarizeResults:
    """
    Tests for T028: Summary statistics generation.
    """

    @pytest.fixture
    def sample_model_results(self):
        """Create a sample model results DataFrame matching T024/T025 output."""
        return pd.DataFrame({
            'model_type': ['rank_ols', 'rank_ols', 'rank_ols', 'spearman'],
            'variable': ['rank_burden', 'sex', 'PC1', 'age'],
            'coefficient': [0.0045, -0.12, 0.003, 0.5],
            'p_value': [0.002, 0.04, 0.15, 0.001],
            'adj_p_value': [0.006, 0.08, 0.30, 0.003]
        })

    @pytest.fixture
    def temp_input_file(self, sample_model_results, tmp_path):
        """Create a temporary input file with sample results."""
        input_path = tmp_path / "model_results.csv"
        sample_model_results.to_csv(input_path, index=False)
        return str(input_path)

    def test_load_model_results_valid(self, temp_input_file):
        """Test loading a valid model results file."""
        df = load_model_results(temp_input_file)
        assert isinstance(df, pd.DataFrame)
        assert 'rank_burden' in df['variable'].values
        assert 'coefficient' in df.columns

    def test_load_model_results_missing_file(self):
        """Test that loading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_model_results("non_existent_file.csv")

    def test_load_model_results_missing_columns(self, tmp_path):
        """Test that loading a file with missing columns raises ValueError."""
        bad_df = pd.DataFrame({'model_type': ['rank_ols'], 'variable': ['x']})
        bad_path = tmp_path / "bad.csv"
        bad_df.to_csv(bad_path, index=False)
        
        with pytest.raises(ValueError, match="missing required columns"):
            load_model_results(str(bad_path))

    def test_extract_summary_statistics(self, sample_model_results):
        """Test extraction of summary statistics filters correctly."""
        summary = extract_summary_statistics(sample_model_results)
        
        # Should only contain rank_ols results
        assert all(summary['model_type'] == 'rank_ols')
        
        # Should contain the primary variable
        assert 'rank_burden' in summary['variable'].values
        
        # Should NOT contain spearman results
        assert 'spearman' not in summary['model_type'].values

    def test_extract_summary_statistics_empty(self):
        """Test extraction when input has no matching rows."""
        empty_df = pd.DataFrame(columns=['model_type', 'variable', 'coefficient', 'p_value', 'adj_p_value'])
        summary = extract_summary_statistics(empty_df)
        assert summary.empty

    def test_write_summary_statistics(self, sample_model_results, tmp_path):
        """Test writing summary statistics to file."""
        summary = extract_summary_statistics(sample_model_results)
        output_path = tmp_path / "analysis_results.csv"
        
        write_summary_statistics(summary, str(output_path))
        
        assert output_path.exists()
        written_df = pd.read_csv(output_path)
        assert len(written_df) == len(summary)
        assert 'rank_burden' in written_df['variable'].values

    def test_write_summary_statistics_empty(self, tmp_path):
        """Test writing an empty summary dataframe."""
        empty_summary = pd.DataFrame(columns=['model_type', 'variable', 'coefficient', 'p_value', 'adj_p_value'])
        output_path = tmp_path / "empty_analysis_results.csv"
        
        write_summary_statistics(empty_summary, str(output_path))
        
        assert output_path.exists()
        written_df = pd.read_csv(output_path)
        assert written_df.empty
        assert 'variable' in written_df.columns