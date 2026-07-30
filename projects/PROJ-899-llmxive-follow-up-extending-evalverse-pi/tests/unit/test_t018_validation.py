"""
Unit tests for T018: Preliminary Validation Gate (FR-009).
"""
import os
import sys
import tempfile
import json
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add src to path if running standalone
if 'src' not in sys.path:
    sys.path.insert(0, 'src')

from src.models.evaluate import run_validation_gate, compute_correlation
from src.config import get_state_root

class TestComputeCorrelation:
    def test_perfect_correlation(self):
        """Test with perfect positive correlation."""
        data = {
            'human_score': [1.0, 2.0, 3.0, 4.0, 5.0],
            'vlm_proxy_score': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        df = pd.DataFrame(data)
        r, p, n = compute_correlation(df, 'human_score', 'vlm_proxy_score')
        assert abs(r - 1.0) < 1e-6
        assert n == 5

    def test_no_correlation(self):
        """Test with no correlation."""
        data = {
            'human_score': [1.0, 2.0, 3.0, 4.0, 5.0],
            'vlm_proxy_score': [5.0, 1.0, 4.0, 2.0, 3.0]
        }
        df = pd.DataFrame(data)
        r, p, n = compute_correlation(df, 'human_score', 'vlm_proxy_score')
        # This specific set might have some correlation, but let's test with random
        # Better test: constant values
        data_const = {
            'human_score': [1.0, 2.0, 3.0, 4.0, 5.0],
            'vlm_proxy_score': [1.0, 1.0, 1.0, 1.0, 1.0]
        }
        df_const = pd.DataFrame(data_const)
        r, p, n = compute_correlation(df_const, 'human_score', 'vlm_proxy_score')
        # Correlation with constant is undefined (nan), handled by np.corrcoef
        # np.corrcoef returns nan for constant arrays
        assert np.isnan(r) or abs(r) < 0.01 # Handle nan or near zero

    def test_missing_values(self):
        """Test handling of missing values."""
        data = {
            'human_score': [1.0, 2.0, np.nan, 4.0, 5.0],
            'vlm_proxy_score': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        df = pd.DataFrame(data)
        r, p, n = compute_correlation(df, 'human_score', 'vlm_proxy_score')
        assert n == 4 # One row dropped

class TestValidationGate:
    @pytest.fixture
    def mock_df(self):
        """Create a mock dataframe with sufficient samples."""
        n = 50
        return pd.DataFrame({
            'human_score': np.random.rand(n),
            'vlm_proxy_score': np.random.rand(n)
        })

    @patch('src.models.evaluate.load_evalverse_metadata')
    @patch('src.models.evaluate.get_state_root')
    @patch('src.models.evaluate.write_json')
    def test_gate_passes_with_human_scores(self, mock_write, mock_state, mock_load, mock_df):
        """Gate should pass if human scores are present."""
        mock_load.return_value = mock_df
        mock_state.return_value = Path(tempfile.gettempdir())
        
        result = run_validation_gate()
        
        assert result["status"] in ["passed", "warning"]
        assert result["human_scores_present"] is True
        assert result["exit_code"] == 0

    @patch('src.models.evaluate.load_evalverse_metadata')
    @patch('src.models.evaluate.get_state_root')
    @patch('src.models.evaluate.write_json')
    def test_gate_fails_without_human_scores(self, mock_write, mock_state, mock_load):
        """Gate should fail if human scores are missing."""
        mock_load.return_value = pd.DataFrame({
            'other_col': [1, 2, 3]
        })
        mock_state.return_value = Path(tempfile.gettempdir())
        
        result = run_validation_gate()
        
        assert result["status"] == "failed"
        assert result["human_scores_present"] is False
        assert result["exit_code"] == 1

    @patch('src.models.evaluate.load_evalverse_metadata')
    @patch('src.models.evaluate.get_state_root')
    @patch('src.models.evaluate.write_json')
    def test_gate_handles_low_sample_size(self, mock_write, mock_state, mock_load):
        """Gate should warn if sample size < 30 but still pass if human scores exist."""
        small_df = pd.DataFrame({
            'human_score': np.random.rand(20),
            'vlm_proxy_score': np.random.rand(20)
        })
        mock_load.return_value = small_df
        mock_state.return_value = Path(tempfile.gettempdir())
        
        result = run_validation_gate(min_samples=30)
        
        # Status might be 'warning' but exit code should be 0 because human scores exist
        assert result["exit_code"] == 0
        assert result["human_scores_present"] is True
        assert result["samples_used"] == 20