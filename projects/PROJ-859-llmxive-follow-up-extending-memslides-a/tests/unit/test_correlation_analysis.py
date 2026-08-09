"""
Unit tests for correlation analysis module.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.correlation_analysis import (
    CorrelationAnalysisError,
    load_correlation_data,
    spearman_correlation,
    run_correlation_analysis,
    interpret_correlation
)
from config import get_config, reset_config


class TestSpearmanCorrelation:
    """Tests for the spearman_correlation function."""

    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        corr, p_val = spearman_correlation(x, y)
        assert abs(corr - 1.0) < 1e-6
        assert p_val == 0.0

    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        corr, p_val = spearman_correlation(x, y)
        assert abs(corr - (-1.0)) < 1e-6
        assert p_val == 0.0

    def test_no_correlation(self):
        """Test with uncorrelated data."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 1, 3, 2, 4])  # Random permutation
        corr, p_val = spearman_correlation(x, y)
        # Should be close to 0, but not exactly due to small sample
        assert abs(corr) < 0.8  # Lenient check for small sample

    def test_single_element(self):
        """Test with single element arrays."""
        x = np.array([1])
        y = np.array([2])
        corr, p_val = spearman_correlation(x, y)
        assert corr == 0.0
        assert p_val == 1.0

    def test_length_mismatch(self):
        """Test with mismatched array lengths."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        with pytest.raises(ValueError):
            spearman_correlation(x, y)


class TestInterpretCorrelation:
    """Tests for the interpret_correlation function."""

    def test_perfect_positive(self):
        interpretation = interpret_correlation(1.0, 0.0)
        assert "positive" in interpretation
        assert "very strong" in interpretation
        assert "statistically significant" in interpretation

    def test_perfect_negative(self):
        interpretation = interpret_correlation(-1.0, 0.0)
        assert "negative" in interpretation
        assert "very strong" in interpretation

    def test_no_correlation(self):
        interpretation = interpret_correlation(0.0, 1.0)
        assert "negligible" in interpretation
        assert "no" in interpretation
        assert "not statistically significant" in interpretation

    def test_moderate_significant(self):
        interpretation = interpret_correlation(0.5, 0.01)
        assert "moderate" in interpretation
        assert "statistically significant" in interpretation


class TestLoadCorrelationData:
    """Tests for the load_correlation_data function."""

    def setup_method(self):
        """Setup temporary directory and mock config."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_data_path = Path(self.temp_dir) / "processed"
        self.processed_data_path.mkdir()

        # Create mock data
        feature_data = {
            "trace_id": ["t1", "t2", "t3"],
            "sequence_entropy": [0.5, 0.8, 0.3],
            "tool_repetition_freq": [0.2, 0.6, 0.1],
            "arg_semantic_variance": [0.4, 0.7, 0.2]
        }
        scores_data = {
            "trace_id": ["t1", "t2", "t3"],
            "score": [0.3, 0.7, 0.2]
        }

        pd.DataFrame(feature_data).to_csv(self.processed_data_path / "feature_matrix.csv", index=False)
        pd.DataFrame(scores_data).to_csv(self.processed_data_path / "per_trace_scores.csv", index=False)

        # Mock config
        self.mock_config = {
            "paths": {
                "processed_data": str(self.processed_data_path)
            }
        }

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('analysis.correlation_analysis.get_config')
    def test_load_success(self, mock_get_config):
        """Test successful loading of data."""
        mock_get_config.return_value = self.mock_config
        
        feature_df, scores_df = load_correlation_data()
        
        assert len(feature_df) == 3
        assert len(scores_df) == 3
        assert "trace_id" in feature_df.columns
        assert "score" in scores_df.columns

    @patch('analysis.correlation_analysis.get_config')
    def test_missing_feature_matrix(self, mock_get_config):
        """Test error when feature matrix is missing."""
        mock_get_config.return_value = {
            "paths": {
                "processed_data": str(Path(self.temp_dir) / "missing")
            }
        }
        
        with pytest.raises(CorrelationAnalysisError, match="Feature matrix not found"):
            load_correlation_data()

    @patch('analysis.correlation_analysis.get_config')
    def test_missing_scores(self, mock_get_config):
        """Test error when scores file is missing."""
        # Create feature matrix but not scores
        feature_path = Path(self.temp_dir) / "processed" / "feature_matrix.csv"
        pd.DataFrame({"trace_id": ["t1"]}).to_csv(feature_path, index=False)
        
        mock_get_config.return_value = {
            "paths": {
                "processed_data": str(Path(self.temp_dir) / "processed")
            }
        }
        
        with pytest.raises(CorrelationAnalysisError, match="Compressibility scores not found"):
            load_correlation_data()


class TestRunCorrelationAnalysis:
    """Tests for the run_correlation_analysis function."""

    def setup_method(self):
        """Setup temporary directory and mock config."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_data_path = Path(self.temp_dir) / "processed"
        self.processed_data_path.mkdir()

        # Create mock data with known correlation
        n = 100
        np.random.seed(42)
        x = np.random.normal(0, 1, n)
        y = 2 * x + np.random.normal(0, 0.5, n)  # Positive correlation

        feature_data = {
            "trace_id": [f"t{i}" for i in range(n)],
            "sequence_entropy": x,
            "tool_repetition_freq": np.random.normal(0, 1, n),
            "arg_semantic_variance": np.random.normal(0, 1, n)
        }
        scores_data = {
            "trace_id": [f"t{i}" for i in range(n)],
            "score": y
        }

        pd.DataFrame(feature_data).to_csv(self.processed_data_path / "feature_matrix.csv", index=False)
        pd.DataFrame(scores_data).to_csv(self.processed_data_path / "per_trace_scores.csv", index=False)

        self.mock_config = {
            "paths": {
                "processed_data": str(self.processed_data_path)
            }
        }

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('analysis.correlation_analysis.get_config')
    def test_analysis_completes(self, mock_get_config):
        """Test that analysis completes successfully."""
        mock_get_config.return_value = self.mock_config
        
        results = run_correlation_analysis()
        
        assert "correlations" in results
        assert "sequence_entropy" in results["correlations"]
        assert "coefficient" in results["correlations"]["sequence_entropy"]
        assert "p_value" in results["correlations"]["sequence_entropy"]
        assert "interpretation" in results["correlations"]["sequence_entropy"]
        
        # Check that sequence_entropy has positive correlation (as we constructed it)
        assert results["correlations"]["sequence_entropy"]["coefficient"] > 0

    @patch('analysis.correlation_analysis.get_config')
    def test_output_structure(self, mock_get_config):
        """Test the structure of the output."""
        mock_get_config.return_value = self.mock_config
        
        results = run_correlation_analysis()
        
        assert results["analysis_type"] == "Spearman Rank Correlation"
        assert "n_samples" in results
        assert len(results["correlations"]) == 3  # Three metrics