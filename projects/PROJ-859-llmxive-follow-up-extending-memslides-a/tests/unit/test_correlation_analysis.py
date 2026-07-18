"""
Unit tests for Spearman Correlation Analysis (T036).

Tests the correlation calculation logic and data loading components.
"""
import json
import math
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from analysis.correlation_analysis import (
    spearman_correlation,
    interpret_correlation,
    run_correlation_analysis,
    main
)


class TestSpearmanCorrelation:
    """Tests for the Spearman correlation calculation."""
    
    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        rho, p_value = spearman_correlation(x, y)
        assert abs(rho - 1.0) < 1e-6
        assert p_value < 0.05
        
    def test_perfect_negative_correlation(self):
        """Test with perfectly anti-correlated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        rho, p_value = spearman_correlation(x, y)
        assert abs(rho - (-1.0)) < 1e-6
        assert p_value < 0.05
        
    def test_no_correlation(self):
        """Test with uncorrelated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 1, 4, 2, 3])  # Random permutation
        rho, p_value = spearman_correlation(x, y)
        # Should not be exactly 0, but close
        assert abs(rho) < 0.8
        
    def test_constant_array(self):
        """Test with constant array (zero variance)."""
        x = np.array([1, 1, 1, 1, 1])
        y = np.array([1, 2, 3, 4, 5])
        rho, p_value = spearman_correlation(x, y)
        assert rho == 0.0
        assert p_value == 1.0
        
    def test_single_element(self):
        """Test with single element."""
        x = np.array([1])
        y = np.array([2])
        rho, p_value = spearman_correlation(x, y)
        assert rho == 0.0
        assert p_value == 1.0
        
    def test_empty_arrays(self):
        """Test with empty arrays."""
        x = np.array([])
        y = np.array([])
        rho, p_value = spearman_correlation(x, y)
        assert rho == 0.0
        assert p_value == 1.0
        
    def test_mismatched_lengths(self):
        """Test with mismatched array lengths."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        rho, p_value = spearman_correlation(x, y)
        assert rho == 0.0
        assert p_value == 1.0


class TestInterpretCorrelation:
    """Tests for correlation interpretation."""
    
    def test_negligible_positive(self):
        assert interpret_correlation(0.05) == "positive negligible"
        
    def test_weak_positive(self):
        assert interpret_correlation(0.2) == "positive weak"
        
    def test_moderate_positive(self):
        assert interpret_correlation(0.45) == "positive moderate"
        
    def test_strong_positive(self):
        assert interpret_correlation(0.65) == "positive strong"
        
    def test_very_strong_positive(self):
        assert interpret_correlation(0.85) == "positive very strong"
        
    def test_negligible_negative(self):
        assert interpret_correlation(-0.05) == "negative negligible"
        
    def test_weak_negative(self):
        assert interpret_correlation(-0.2) == "negative weak"
        
    def test_moderate_negative(self):
        assert interpret_correlation(-0.45) == "negative moderate"
        
    def test_strong_negative(self):
        assert interpret_correlation(-0.65) == "negative strong"
        
    def test_very_strong_negative(self):
        assert interpret_correlation(-0.85) == "negative very strong"


class TestRunCorrelationAnalysis:
    """Tests for the full correlation analysis pipeline."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        import pandas as pd
        data = {
            "trace_id": ["t1", "t2", "t3", "t4", "t5"],
            "sequence_entropy": [1.0, 2.0, 3.0, 4.0, 5.0],
            "tool_repetition_frequency": [0.1, 0.2, 0.3, 0.4, 0.5],
            "argument_semantic_variance": [0.5, 0.6, 0.7, 0.8, 0.9],
            "compressibility_score": [0.9, 0.8, 0.7, 0.6, 0.5]
        }
        return pd.DataFrame(data)
        
    def test_analysis_runs_successfully(self, sample_dataframe):
        """Test that analysis runs without errors."""
        metrics_cols = ["sequence_entropy", "tool_repetition_frequency"]
        target_col = "compressibility_score"
        
        results = run_correlation_analysis(
            sample_dataframe, metrics_cols, target_col
        )
        
        assert "method" in results
        assert results["method"] == "Spearman"
        assert results["sample_size"] == 5
        assert len(results["correlations"]) == 2
        
    def test_correlation_results_structure(self, sample_dataframe):
        """Test that correlation results have correct structure."""
        metrics_cols = ["sequence_entropy"]
        target_col = "compressibility_score"
        
        results = run_correlation_analysis(
            sample_dataframe, metrics_cols, target_col
        )
        
        corr = results["correlations"][0]
        assert "metric" in corr
        assert "correlation_coefficient" in corr
        assert "p_value" in corr
        assert "significant_at_0.05" in corr
        assert "significant_at_0.01" in corr
        assert "interpretation" in corr
        
    def test_handles_missing_columns(self, sample_dataframe):
        """Test that missing columns are handled gracefully."""
        metrics_cols = ["nonexistent_column", "sequence_entropy"]
        target_col = "compressibility_score"
        
        results = run_correlation_analysis(
            sample_dataframe, metrics_cols, target_col
        )
        
        # Should only have one result for the existing column
        assert len(results["correlations"]) == 1


class TestMainFunction:
    """Tests for the main entry point."""
    
    @patch("analysis.correlation_analysis.get_config")
    @patch("analysis.correlation_analysis.load_correlation_data")
    @patch("analysis.correlation_analysis.run_correlation_analysis")
    @patch("builtins.open")
    def test_main_success(
        self, mock_open, mock_run_analysis, mock_load_data, mock_get_config
    ):
        """Test successful execution of main."""
        mock_config = {
            "paths": {"processed": "/tmp"}
        }
        mock_get_config.return_value = mock_config
        
        mock_df = Mock()
        mock_load_data.return_value = mock_df
        
        mock_results = {
            "method": "Spearman",
            "correlations": []
        }
        mock_run_analysis.return_value = mock_results
        
        result = main()
        
        assert result == 0
        mock_load_data.assert_called_once()
        mock_run_analysis.assert_called_once()
        
    @patch("analysis.correlation_analysis.get_config")
    @patch("analysis.correlation_analysis.load_correlation_data")
    def test_main_file_not_found(self, mock_load_data, mock_get_config):
        """Test handling of missing data files."""
        mock_config = {"paths": {"processed": "/tmp"}}
        mock_get_config.return_value = mock_config
        mock_load_data.side_effect = FileNotFoundError("Test error")
        
        result = main()
        
        assert result == 1