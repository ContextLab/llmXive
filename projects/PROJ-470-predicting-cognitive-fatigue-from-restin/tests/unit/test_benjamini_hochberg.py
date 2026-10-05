"""Tests for Benjamini-Hochberg correction module.

This test suite verifies that the BH correction is applied correctly
to correlation p-values and that the output file is generated as expected.
"""
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from statsmodels.stats.multitest import multipletests

# Import the module under test
# Adjust import path based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from benjamini_hochberg import (
    load_raw_correlation_results,
    run_benjamini_hochberg,
    save_corrected_results,
    main
)


class TestLoadRawCorrelationResults:
    """Tests for loading raw correlation results."""

    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        # Create a temporary CSV file
        csv_path = tmp_path / "raw_correlations.csv"
        data = {
            'electrode': ['Fz', 'Cz', 'Pz'],
            'p_value': [0.01, 0.03, 0.05],
            'correlation_type': ['pearson', 'pearson', 'spearman']
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)

        # Load and verify
        loaded_df = load_raw_correlation_results(str(csv_path))

        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ['electrode', 'p_value', 'correlation_type']
        assert list(loaded_df['electrode']) == ['Fz', 'Cz', 'Pz']

    def test_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_raw_correlation_results(str(tmp_path / "nonexistent.csv"))

    def test_missing_columns(self, tmp_path):
        """Test that ValueError is raised for missing required columns."""
        csv_path = tmp_path / "incomplete.csv"
        data = {
            'electrode': ['Fz'],
            'p_value': [0.01]
            # Missing 'correlation_type'
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)

        with pytest.raises(ValueError) as exc_info:
            load_raw_correlation_results(str(csv_path))

        assert 'correlation_type' in str(exc_info.value)


class TestRunBenjaminiHochberg:
    """Tests for the BH correction algorithm."""

    def test_correction_applied(self):
        """Test that BH correction is applied to p-values."""
        data = {
            'electrode': ['Fz', 'Cz', 'Pz', 'Oz'],
            'p_value': [0.01, 0.02, 0.03, 0.04],
            'correlation_type': ['pearson'] * 4
        }
        df = pd.DataFrame(data)

        corrected_df = run_benjamini_hochberg(df, alpha=0.05)

        # Verify new columns exist
        assert 'p_corrected' in corrected_df.columns
        assert 'is_significant' in corrected_df.columns

        # Verify p_corrected values are different from raw (unless all 1.0)
        assert not corrected_df['p_corrected'].equals(corrected_df['p_value'])

    def test_significance_flagging(self):
        """Test that significant results are flagged correctly."""
        # Create data where some should be significant after correction
        data = {
            'electrode': ['Fz', 'Cz', 'Pz'],
            'p_value': [0.001, 0.01, 0.5],
            'correlation_type': ['pearson'] * 3
        }
        df = pd.DataFrame(data)

        corrected_df = run_benjamini_hochberg(df, alpha=0.05)

        # The smallest p-value should likely be significant
        assert corrected_df.iloc[0]['is_significant'] is True

        # The largest p-value should likely not be significant
        assert corrected_df.iloc[2]['is_significant'] is False

    def test_different_alpha(self):
        """Test that different alpha values affect significance."""
        data = {
            'electrode': ['Fz'],
            'p_value': [0.04],
            'correlation_type': ['pearson']
        }
        df = pd.DataFrame(data)

        # With alpha=0.05, might be significant
        result_05 = run_benjamini_hochberg(df, alpha=0.05)

        # With alpha=0.01, likely not significant
        result_01 = run_benjamini_hochberg(df, alpha=0.01)

        # At least one should be False for the stricter alpha
        assert result_01.iloc[0]['is_significant'] == False or result_05.iloc[0]['is_significant'] == False


class TestSaveCorrectedResults:
    """Tests for saving corrected results."""

    def test_save_and_reload(self, tmp_path):
        """Test that saved results can be reloaded correctly."""
        output_path = tmp_path / "corrected.csv"

        data = {
            'electrode': ['Fz', 'Cz'],
            'p_value': [0.01, 0.02],
            'correlation_type': ['pearson', 'pearson'],
            'p_corrected': [0.015, 0.025],
            'is_significant': [True, False]
        }
        df = pd.DataFrame(data)

        save_corrected_results(df, str(output_path))

        # Verify file exists
        assert output_path.exists()

        # Reload and verify content
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 2
        assert list(loaded_df.columns) == list(df.columns)

    def test_creates_directories(self, tmp_path):
        """Test that save creates parent directories if needed."""
        nested_path = tmp_path / "subdir" / "corrected.csv"

        data = {
            'electrode': ['Fz'],
            'p_value': [0.01],
            'correlation_type': ['pearson'],
            'p_corrected': [0.015],
            'is_significant': [True]
        }
        df = pd.DataFrame(data)

        save_corrected_results(df, str(nested_path))

        assert nested_path.exists()


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline(self, tmp_path):
        """Test the full BH correction pipeline."""
        # Setup input
        input_path = tmp_path / "raw.csv"
        output_path = tmp_path / "corrected.csv"

        data = {
            'electrode': [f'ch_{i}' for i in range(10)],
            'p_value': [0.01 * (i + 1) for i in range(10)],
            'correlation_type': ['pearson'] * 10
        }
        pd.DataFrame(data).to_csv(input_path, index=False)

        # Load, correct, and save
        raw_df = load_raw_correlation_results(str(input_path))
        corrected_df = run_benjamini_hochberg(raw_df, alpha=0.05)
        save_corrected_results(corrected_df, str(output_path))

        # Verify output
        assert output_path.exists()
        result_df = pd.read_csv(output_path)

        assert len(result_df) == 10
        assert 'p_corrected' in result_df.columns
        assert 'is_significant' in result_df.columns

        # Verify at least one significant result (the smallest p-value)
        assert result_df['is_significant'].sum() >= 1