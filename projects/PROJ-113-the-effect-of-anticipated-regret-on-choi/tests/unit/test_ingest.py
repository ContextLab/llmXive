"""
Unit tests for data ingestion utilities.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from ingest import apply_deferral_flags, generate_regret_proxy_dataset
from config import get_path

class TestApplyDeferralFlags:
    """Tests for the apply_deferral_flags function."""

    def test_deferral_with_timeout_and_no_action(self):
        """Test that deferral is set to 1 when timeout=True and action is missing."""
        df = pd.DataFrame({
            'timeout': [True, False, True, False],
            'action': [None, 'buy', None, 'sell']
        })
        
        result = apply_deferral_flags(df)
        
        assert result['deferral'].tolist() == [1, 0, 1, 0]

    def test_deferral_with_timeout_numeric(self):
        """Test that deferral works with numeric timeout values (1=True)."""
        df = pd.DataFrame({
            'timeout': [1, 0, 1, 0],
            'action': ['', 'buy', '', 'sell']
        })
        
        result = apply_deferral_flags(df)
        
        assert result['deferral'].tolist() == [1, 0, 1, 0]

    def test_no_deferral_when_action_taken(self):
        """Test that deferral is 0 when action is taken, even with timeout."""
        df = pd.DataFrame({
            'timeout': [True, True],
            'action': ['buy', 'sell']
        })
        
        result = apply_deferral_flags(df)
        
        assert result['deferral'].tolist() == [0, 0]

    def test_missing_columns_fallback(self):
        """Test that missing columns result in all deferral=0."""
        df = pd.DataFrame({
            'other_col': [1, 2, 3]
        })
        
        result = apply_deferral_flags(df)
        
        assert result['deferral'].tolist() == [0, 0, 0]

class TestGenerateRegretProxyDataset:
    """Tests for the generate_regret_proxy_dataset function."""

    @patch('ingest.load_huggingface_dataset')
    @patch('ingest.add_regret_and_loss_metrics')
    @patch('ingest.add_perceived_risk_covariate')
    @patch('ingest.ensure_paths_exist')
    def test_generates_output_file(self, mock_ensure, mock_add_risk, mock_add_regret, mock_load):
        """Test that the function generates the output CSV file."""
        # Mock the dataset loading
        mock_df = pd.DataFrame({
            'timeout': [True, False, True],
            'action': [None, 'buy', None],
            'options': [[1, 2], [3, 4], [5, 6]]
        })
        mock_load.return_value = mock_df
        
        # Mock the feature functions to return the same df
        mock_add_regret.return_value = mock_df.copy()
        mock_add_regret.return_value['regret_proxy'] = [0.5, 0.0, 0.3]
        mock_add_risk.return_value = mock_add_regret.return_value
        
        # Run the function
        output_path = get_path("data/processed/test_output.csv")
        generate_regret_proxy_dataset("test/dataset", "data/processed/test_output.csv")
        
        # Verify the file was created
        assert output_path.exists()
        
        # Verify the content
        result_df = pd.read_csv(output_path)
        assert 'regret_proxy' in result_df.columns
        assert 'deferral' in result_df.columns
        assert len(result_df) == 3

    @patch('ingest.load_huggingface_dataset')
    def test_handles_missing_required_columns(self, mock_load):
        """Test that the function raises an error when required columns are missing."""
        # Mock a dataset without required columns
        mock_df = pd.DataFrame({
            'other_col': [1, 2, 3]
        })
        mock_load.return_value = mock_df
        
        with pytest.raises(ValueError, match="Missing required column"):
            generate_regret_proxy_dataset("test/dataset", "data/processed/test_output.csv")