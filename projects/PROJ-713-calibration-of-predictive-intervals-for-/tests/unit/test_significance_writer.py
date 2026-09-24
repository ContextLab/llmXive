"""
Unit tests for T032: significance_writer module.

Tests verify that write_significance_results correctly serializes
bootstrap p-values to results/significance_test.csv with the required schema.
"""

import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from evaluation.significance_writer import (
    load_bootstrap_results,
    write_significance_results,
    main
)
from utils.exceptions import DataValidationError, ConfigurationError


class TestLoadBootstrapResults:
    """Tests for load_bootstrap_results function."""

    def test_load_from_default_path(self, tmp_path, monkeypatch):
        """Test loading from default RESULTS_DIR path."""
        # Setup mock results directory
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        # Create mock bootstrap file
        mock_data = pd.DataFrame({
            'model_a': ['ARIMA', 'Prophet'],
            'model_b': ['Prophet', 'LSTM'],
            'metric': ['coverage_deviation', 'coverage_deviation'],
            'p_value': [0.03, 0.15]
        })
        mock_file = results_dir / "bootstrap_results.csv"
        mock_data.to_csv(mock_file, index=False)
        
        # Patch RESULTS_DIR
        monkeypatch.setattr('evaluation.significance_writer.RESULTS_DIR', results_dir)
        
        # Load and verify
        df = load_bootstrap_results()
        assert len(df) == 2
        assert set(df.columns) == {'model_a', 'model_b', 'metric', 'p_value'}
        assert df.iloc[0]['p_value'] == 0.03

    def test_load_from_custom_path(self, tmp_path):
        """Test loading from a custom path."""
        custom_file = tmp_path / "custom_bootstrap.csv"
        mock_data = pd.DataFrame({
            'model_a': ['X'],
            'model_b': ['Y'],
            'metric': ['test_metric'],
            'p_value': [0.5]
        })
        mock_data.to_csv(custom_file, index=False)
        
        df = load_bootstrap_results(str(custom_file))
        assert len(df) == 1
        assert df.iloc[0]['model_a'] == 'X'

    def test_missing_file_raises_error(self, tmp_path, monkeypatch):
        """Test that missing file raises DataValidationError."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        monkeypatch.setattr('evaluation.significance_writer.RESULTS_DIR', results_dir)
        
        with pytest.raises(DataValidationError, match="Bootstrap results file not found"):
            load_bootstrap_results()

    def test_missing_columns_raises_error(self, tmp_path):
        """Test that missing columns raise DataValidationError."""
        custom_file = tmp_path / "bad_bootstrap.csv"
        bad_data = pd.DataFrame({
            'model_a': ['X'],
            'model_b': ['Y'],
            # Missing 'metric' and 'p_value'
        })
        bad_data.to_csv(custom_file, index=False)
        
        with pytest.raises(DataValidationError, match="missing required columns"):
            load_bootstrap_results(str(custom_file))


class TestWriteSignificanceResults:
    """Tests for write_significance_results function."""

    def test_writes_correct_schema(self, tmp_path):
        """Test that output CSV has correct columns and order."""
        input_df = pd.DataFrame({
            'model_a': ['ARIMA'],
            'model_b': ['Prophet'],
            'metric': ['coverage_deviation'],
            'p_value': [0.02]
        })
        
        output_file = tmp_path / "significance_test.csv"
        result_df = write_significance_results(input_df, output_path=str(output_file))
        
        # Verify file exists
        assert output_file.exists()
        
        # Verify columns
        assert list(result_df.columns) == ['model_a', 'model_b', 'metric', 'p_value', 'significant']
        
        # Verify significance calculation
        assert result_df.iloc[0]['significant'] == True

    def test_significance_threshold(self, tmp_path):
        """Test that significance is calculated correctly against alpha."""
        input_df = pd.DataFrame({
            'model_a': ['A', 'B', 'C'],
            'model_b': ['X', 'Y', 'Z'],
            'metric': ['m', 'm', 'm'],
            'p_value': [0.01, 0.05, 0.10]
        })
        
        output_file = tmp_path / "sig.csv"
        result_df = write_significance_results(input_df, alpha=0.05, output_path=str(output_file))
        
        # 0.01 < 0.05 -> True
        # 0.05 < 0.05 -> False
        # 0.10 < 0.05 -> False
        assert result_df.iloc[0]['significant'] == True
        assert result_df.iloc[1]['significant'] == False
        assert result_df.iloc[2]['significant'] == False

    def test_empty_input_raises_error(self, tmp_path):
        """Test that empty input raises DataValidationError."""
        empty_df = pd.DataFrame(columns=['model_a', 'model_b', 'metric', 'p_value'])
        output_file = tmp_path / "out.csv"
        
        with pytest.raises(DataValidationError, match="Input bootstrap DataFrame is empty"):
            write_significance_results(empty_df, output_path=str(output_file))

    def test_missing_input_columns_raises_error(self, tmp_path):
        """Test that missing input columns raise DataValidationError."""
        bad_df = pd.DataFrame({
            'model_a': ['X'],
            'model_b': ['Y']
            # Missing metric, p_value
        })
        output_file = tmp_path / "out.csv"
        
        with pytest.raises(DataValidationError, match="missing required columns"):
            write_significance_results(bad_df, output_path=str(output_file))

    def test_creates_output_directory(self, tmp_path):
        """Test that function creates output directory if missing."""
        input_df = pd.DataFrame({
            'model_a': ['A'],
            'model_b': ['B'],
            'metric': ['m'],
            'p_value': [0.01]
        })
        
        nested_dir = tmp_path / "nested" / "results"
        output_file = nested_dir / "sig.csv"
        
        # Directory doesn't exist yet
        assert not nested_dir.exists()
        
        write_significance_results(input_df, output_path=str(output_file))
        
        assert output_file.exists()


class TestMain:
    """Tests for CLI main function."""

    def test_main_success(self, tmp_path, monkeypatch, caplog):
        """Test successful execution of main."""
        # Setup
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        
        bootstrap_data = pd.DataFrame({
            'model_a': ['ARIMA'],
            'model_b': ['Prophet'],
            'metric': ['coverage'],
            'p_value': [0.02]
        })
        bootstrap_file = results_dir / "bootstrap_results.csv"
        bootstrap_data.to_csv(bootstrap_file, index=False)
        
        monkeypatch.setattr('evaluation.significance_writer.RESULTS_DIR', results_dir)
        
        # Mock sys.argv
        monkeypatch.setattr('sys.argv', ['test', '--output', str(tmp_path / "out.csv")])
        
        # Run
        exit_code = main()
        
        assert exit_code == 0
        assert (tmp_path / "out.csv").exists()

    def test_main_file_not_found(self, tmp_path, monkeypatch):
        """Test main returns error code when file not found."""
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        monkeypatch.setattr('evaluation.significance_writer.RESULTS_DIR', results_dir)
        
        monkeypatch.setattr('sys.argv', ['test'])
        
        exit_code = main()
        
        assert exit_code == 1