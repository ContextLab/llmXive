import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Adjust imports to match project structure if running from root
# Assuming tests are run from project root or sys.path includes code/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analysis.summarize_results import load_model_results, extract_summary_statistics, write_summary_statistics

class TestSummarizeResults:
    def test_load_model_results_success(self, tmp_path):
        """Test successful loading of model results CSV."""
        input_file = tmp_path / "model_results.csv"
        data = {
            'term': ['rank(burden)', 'sex', 'PC1', 'spearman_correlation'],
            'coefficient': [0.15, -0.05, 0.02, 0.25],
            'p_value': [0.001, 0.04, 0.10, 0.0001],
            'adj_p_value': [0.005, 0.06, 0.15, 0.0005],
            'model_type': ['rank_ols', 'rank_ols', 'rank_ols', 'spearman']
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)

        result = load_model_results(input_file)
        assert len(result) == 4
        assert 'rank(burden)' in result['term'].values
        assert 'spearman_correlation' in result['term'].values

    def test_load_model_results_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing input."""
        input_file = tmp_path / "non_existent.csv"
        with pytest.raises(FileNotFoundError):
            load_model_results(input_file)

    def test_load_model_results_missing_columns(self, tmp_path):
        """Test that ValueError is raised if required columns are missing."""
        input_file = tmp_path / "model_results.csv"
        data = {
            'term': ['rank(burden)'],
            'coefficient': [0.15]
            # Missing p_value and adj_p_value
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)

        with pytest.raises(ValueError, match="missing required columns"):
            load_model_results(input_file)

    def test_extract_summary_statistics(self, tmp_path):
        """Test extraction of summary statistics from model results."""
        input_file = tmp_path / "model_results.csv"
        data = {
            'term': ['rank(burden)', 'sex', 'spearman_correlation'],
            'coefficient': [0.15, -0.05, 0.25],
            'p_value': [0.001, 0.04, 0.0001],
            'adj_p_value': [0.005, 0.06, 0.0005],
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)

        loaded_df = load_model_results(input_file)
        summary = extract_summary_statistics(loaded_df)

        assert not summary.empty
        assert 'metric' in summary.columns
        
        # Check for Rank-OLS burden
        ols_row = summary[summary['metric'] == 'rank_ols_burden_coefficient']
        assert not ols_row.empty
        assert abs(ols_row['value'].iloc[0] - 0.15) < 1e-6
        
        # Check for Spearman
        spear_row = summary[summary['metric'] == 'spearman_correlation']
        assert not spear_row.empty
        assert abs(spear_row['value'].iloc[0] - 0.25) < 1e-6

    def test_write_summary_statistics(self, tmp_path):
        """Test writing summary statistics to CSV."""
        output_file = tmp_path / "analysis_results.csv"
        summary_data = {
            'metric': ['rank_ols_burden_coefficient'],
            'value': [0.15],
            'p_value': [0.001],
            'adj_p_value': [0.005],
            'model': ['Rank-OLS']
        }
        summary_df = pd.DataFrame(summary_data)

        write_summary_statistics(summary_df, output_file)

        assert output_file.exists()
        result_df = pd.read_csv(output_file)
        assert len(result_df) == 1
        assert result_df['metric'].iloc[0] == 'rank_ols_burden_coefficient'
        assert result_df['value'].iloc[0] == 0.15