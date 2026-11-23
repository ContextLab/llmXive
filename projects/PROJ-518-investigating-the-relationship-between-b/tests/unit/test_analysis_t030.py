"""
Unit tests for T030: Saving permutation and sensitivity results.

Verifies that the save functions correctly write files with the required schema.
"""
import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.saving import save_permutation_results, save_sensitivity_summary
from analysis.statistics import construct_sensitivity_df

class TestSavePermutationResults:
    def test_save_permutation_results_schema(self, tmp_path):
        """Test that permutation results are saved with correct schema."""
        # Create mock data
        data = {
            'shuffle_id': [1, 2, 3, 4, 5],
            'correlation': [0.1, 0.2, 0.15, 0.25, 0.05]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "permutation_results.csv"
        save_permutation_results(df, output_path=str(output_path))
        
        assert output_path.exists(), "Output file was not created."
        
        loaded_df = pd.read_csv(output_path)
        assert list(loaded_df.columns) == ['shuffle_id', 'correlation'], "Schema mismatch."
        assert len(loaded_df) == 5, "Row count mismatch."

    def test_save_permutation_results_missing_columns(self, tmp_path):
        """Test that ValueError is raised if columns are missing."""
        data = {
            'shuffle_id': [1, 2, 3],
            # Missing 'correlation'
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "permutation_results.csv"
        
        with pytest.raises(ValueError, match="DataFrame must contain columns"):
            save_permutation_results(df, output_path=str(output_path))

class TestSaveSensitivitySummary:
    def test_save_sensitivity_summary_schema(self, tmp_path):
        """Test that sensitivity summary is saved with correct schema."""
        # Create mock data
        data = {
            'window_length': [20, 30, 40],
            'correlation': [0.45, 0.42, 0.48],
            'empirical_p_value': [0.01, 0.03, 0.005]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "sensitivity_summary.csv"
        save_sensitivity_summary(df, output_path=str(output_path))
        
        assert output_path.exists(), "Output file was not created."
        
        loaded_df = pd.read_csv(output_path)
        assert list(loaded_df.columns) == ['window_length', 'correlation', 'empirical_p_value'], "Schema mismatch."
        assert len(loaded_df) == 3, "Row count mismatch."
        # Check that empirical_p_value is non-null
        assert loaded_df['empirical_p_value'].notnull().all(), "empirical_p_value contains nulls."

    def test_save_sensitivity_summary_missing_columns(self, tmp_path):
        """Test that ValueError is raised if columns are missing."""
        data = {
            'window_length': [20, 30],
            'correlation': [0.45, 0.42],
            # Missing 'empirical_p_value'
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "sensitivity_summary.csv"
        
        with pytest.raises(ValueError, match="DataFrame must contain columns"):
            save_sensitivity_summary(df, output_path=str(output_path))

class TestConstructSensitivityDf:
    def test_construct_sensitivity_df_columns(self):
        """Test that construct_sensitivity_df produces the correct columns."""
        # Mock data from T046
        data = {
            'p_values': [0.01, 0.05, 0.02],
            'correlations': [0.4, 0.35, 0.45],
            'window_lengths': [20, 30, 40]
        }
        
        df = construct_sensitivity_df(data)
        
        assert 'window_length' in df.columns, "Missing window_length column."
        assert 'correlation' in df.columns, "Missing correlation column."
        assert 'empirical_p_value' in df.columns, "Missing empirical_p_value column."
        
        # Verify data types and values
        assert df['window_length'].tolist() == [20, 30, 40]
        assert df['correlation'].tolist() == [0.4, 0.35, 0.45]
        assert df['empirical_p_value'].tolist() == [0.01, 0.05, 0.02]