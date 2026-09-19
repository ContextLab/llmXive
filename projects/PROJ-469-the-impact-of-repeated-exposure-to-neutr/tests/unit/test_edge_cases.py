"""
Unit tests for edge cases in the llmXive political bias pipeline.
Tests cover:
1. Missing columns in data loading
2. Missingness > 50% in preprocessing
3. Bootstrap timeout in robustness checks
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import time
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import from the project code
from code.data_loader import check_required_columns, load_project_implicit_data
from code.preprocessing import impute_mice
from code.robustness import run_alpha_sweep
from code.config_manager import get_config


class TestDataLoaderEdgeCases:
    """Tests for data loading edge cases."""

    def test_check_required_columns_missing_column(self):
        """Test that ValueError is raised when a required column is missing."""
        df = pd.DataFrame({
            'IAT_D_score': [0.1, 0.2, 0.3],
            'political_ideology': [-1, 0, 1]
            # Missing 'news_exposure_freq'
        })
        required_cols = ['IAT_D_score', 'political_ideology', 'news_exposure_freq']

        with pytest.raises(ValueError) as excinfo:
            check_required_columns(df, required_cols)

        assert 'news_exposure_freq' in str(excinfo.value)
        assert 'Missing required columns' in str(excinfo.value)

    def test_check_required_columns_all_present(self):
        """Test that no error is raised when all required columns are present."""
        df = pd.DataFrame({
            'IAT_D_score': [0.1, 0.2, 0.3],
            'political_ideology': [-1, 0, 1],
            'news_exposure_freq': [1, 2, 3]
        })
        required_cols = ['IAT_D_score', 'political_ideology', 'news_exposure_freq']

        # Should not raise
        check_required_columns(df, required_cols)

    def test_load_project_implicit_data_missing_columns(self):
        """Test that load_project_implicit_data raises ValueError on missing columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a CSV with missing columns
            csv_path = os.path.join(tmpdir, 'test_data.csv')
            df_missing = pd.DataFrame({
                'IAT_D_score': [0.1, 0.2, 0.3],
                'political_ideology': [-1, 0, 1]
                # Missing 'news_exposure_freq'
            })
            df_missing.to_csv(csv_path, index=False)

            with patch('code.data_loader.get_data_raw_path') as mock_path:
                mock_path.return_value = Path(tmpdir)

                with pytest.raises(ValueError) as excinfo:
                    load_project_implicit_data()

                assert 'news_exposure_freq' in str(excinfo.value)


class TestPreprocessingEdgeCases:
    """Tests for preprocessing edge cases."""

    def test_impute_mice_missingness_exceeds_threshold(self):
        """Test that impute_mice raises ValueError when missingness > 50%."""
        # Create data with >50% missingness in a column
        df = pd.DataFrame({
            'IAT_D_score': [0.1, 0.2, np.nan, np.nan, np.nan],  # 60% missing
            'political_ideology': [-1, 0, 1, -1, 0],
            'news_exposure_freq': [1, 2, 3, 4, 5]
        })

        with pytest.raises(ValueError) as excinfo:
            impute_mice(df, max_missingness=0.50)

        assert 'Missingness exceeds' in str(excinfo.value)
        assert 'IAT_D_score' in str(excinfo.value)

    def test_impute_mice_missingness_at_threshold(self):
        """Test that impute_mice works when missingness is exactly at threshold."""
        # Create data with exactly 50% missingness
        df = pd.DataFrame({
            'IAT_D_score': [0.1, np.nan, 0.3, np.nan],  # 50% missing
            'political_ideology': [-1, 0, 1, -1],
            'news_exposure_freq': [1, 2, 3, 4]
        })

        # Should not raise
        imputed_df = impute_mice(df, max_missingness=0.50)
        assert imputed_df is not None
        assert not imputed_df.isnull().any().any()

    def test_impute_mice_no_missingness(self):
        """Test that impute_mice works when there is no missingness."""
        df = pd.DataFrame({
            'IAT_D_score': [0.1, 0.2, 0.3],
            'political_ideology': [-1, 0, 1],
            'news_exposure_freq': [1, 2, 3]
        })

        imputed_df = impute_mice(df, max_missingness=0.50)
        assert imputed_df is not None
        assert not imputed_df.isnull().any().any()


class TestRobustnessEdgeCases:
    """Tests for robustness check edge cases."""

    @patch('code.robustness.time.time')
    def test_run_alpha_sweep_timeout(self, mock_time):
        """Test that run_alpha_sweep raises TimeoutError when execution exceeds timeout."""
        # Setup mock to simulate timeout
        mock_time.side_effect = [0, 100]  # Start at 0, end at 100 seconds

        df = pd.DataFrame({
            'IAT_D_score': [0.1, 0.2, 0.3, 0.4, 0.5] * 20,
            'news_exposure_z': [0.1, -0.1, 0.2, -0.2, 0.3] * 20,
            'political_ideology': [-1, 0, 1, -1, 0] * 20
        })

        # Very short timeout (1 second)
        timeout = 1.0

        with pytest.raises(TimeoutError) as excinfo:
            run_alpha_sweep(df, timeout=timeout)

        assert 'Timeout' in str(excinfo.value)

    def test_run_alpha_sweep_empty_dataframe(self):
        """Test that run_alpha_sweep handles empty dataframe."""
        df = pd.DataFrame({
            'IAT_D_score': [],
            'news_exposure_z': [],
            'political_ideology': []
        })

        # Should handle empty data gracefully (return empty results or raise appropriate error)
        with pytest.raises((ValueError, RuntimeError)):
            run_alpha_sweep(df, timeout=60)

    def test_run_alpha_sweep_single_row(self):
        """Test that run_alpha_sweep handles single row dataframe."""
        df = pd.DataFrame({
            'IAT_D_score': [0.1],
            'news_exposure_z': [0.1],
            'political_ideology': [0]
        })

        # Should handle single row gracefully
        with pytest.raises((ValueError, RuntimeError)):
            run_alpha_sweep(df, timeout=60)


class TestIntegrationEdgeCases:
    """Integration tests for multiple edge cases."""

    def test_pipeline_with_high_missingness(self):
        """Test that the pipeline fails appropriately with high missingness."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create data with >50% missingness
            df = pd.DataFrame({
                'IAT_D_score': [0.1, np.nan, np.nan, np.nan, np.nan],
                'political_ideology': [-1, 0, 1, -1, 0],
                'news_exposure_freq': [1, 2, 3, 4, 5]
            })
            csv_path = os.path.join(tmpdir, 'test_data.csv')
            df.to_csv(csv_path, index=False)

            # Verify that the data loader catches this before preprocessing
            with patch('code.data_loader.get_data_raw_path') as mock_path:
                mock_path.return_value = Path(tmpdir)

                # Should raise ValueError during loading/validation
                with pytest.raises(ValueError):
                    load_project_implicit_data()

    def test_robustness_with_invalid_alpha_levels(self):
        """Test that robustness checks handle invalid alpha levels."""
        df = pd.DataFrame({
            'IAT_D_score': [0.1, 0.2, 0.3, 0.4, 0.5] * 20,
            'news_exposure_z': [0.1, -0.1, 0.2, -0.2, 0.3] * 20,
            'political_ideology': [-1, 0, 1, -1, 0] * 20
        })

        # Invalid alpha levels (negative, > 1)
        invalid_alphas = [-0.1, 1.5, 0.05]

        # Should raise ValueError for invalid alpha levels
        with pytest.raises(ValueError):
            run_alpha_sweep(df, alphas=invalid_alphas, timeout=60)

    def test_robustness_with_nan_values(self):
        """Test that robustness checks handle NaN values in data."""
        df = pd.DataFrame({
            'IAT_D_score': [0.1, np.nan, 0.3, 0.4, 0.5] * 20,
            'news_exposure_z': [0.1, -0.1, np.nan, -0.2, 0.3] * 20,
            'political_ideology': [-1, 0, 1, -1, 0] * 20
        })

        # Should raise error or handle NaN appropriately
        # The function should either impute first or raise an error
        with pytest.raises((ValueError, RuntimeError)):
            run_alpha_sweep(df, timeout=60)