"""
Unit tests for validation utilities in code/utils/validation.py
"""
import logging
import warnings
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from code.utils.validation import (
    calculate_vif,
    get_high_vif_predictors,
    handle_error,
    setup_logger,
)


class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_returns_logger(self):
        """Logger should return a logging.Logger instance."""
        logger = setup_logger('test_logger')
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_logger'

    def test_setup_logger_with_string_level(self):
        """Logger should accept string level names."""
        logger = setup_logger('test_string_level', level='DEBUG')
        assert logger.level == logging.DEBUG

    def test_setup_logger_with_int_level(self):
        """Logger should accept integer level values."""
        logger = setup_logger('test_int_level', level=logging.WARNING)
        assert logger.level == logging.WARNING

    def test_setup_logger_reuses_existing(self):
        """Logger should reuse existing handler if already configured."""
        logger1 = setup_logger('test_reuse', level='INFO')
        logger2 = setup_logger('test_reuse', level='DEBUG')
        # Should have same handlers count (not duplicated)
        assert len(logger1.handlers) == len(logger2.handlers)


class TestHandleError:
    """Tests for handle_error function."""

    def test_handle_error_warning_level(self):
        """Warning level should emit a warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            handle_error('Test warning message', 'warning')
            assert len(w) == 1
            assert 'Test warning message' in str(w[0].message)

    def test_handle_error_error_level_raises(self):
        """Error level should raise ValueError."""
        with pytest.raises(ValueError, match='Test error message'):
            handle_error('Test error message', 'error')

    def test_handle_error_critical_level_raises(self):
        """Critical level should raise RuntimeError."""
        with pytest.raises(RuntimeError, match='Test critical message'):
            handle_error('Test critical message', 'critical')

    def test_handle_error_invalid_level_raises(self):
        """Invalid level should raise ValueError."""
        with pytest.raises(ValueError, match='Invalid level'):
            handle_error('Test message', 'invalid_level')

    def test_handle_error_debug_level_logs(self):
        """Debug level should log without raising."""
        with patch('code.utils.validation.setup_logger') as mock_logger:
            mock_logger.return_value.debug = lambda msg: None
            handle_error('Test debug message', 'debug')
            mock_logger.return_value.debug.assert_called_once()


class TestCalculateVIF:
    """Tests for calculate_vif function."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample dataframe for VIF testing."""
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'A': np.random.randn(n),
            'B': np.random.randn(n),
            'C': np.random.randn(n),
            'D': np.random.randn(n),
        })

    def test_calculate_vif_returns_dataframe(self, sample_dataframe):
        """VIF calculation should return a DataFrame."""
        vif_df = calculate_vif(sample_dataframe, ['A', 'B', 'C'])
        assert isinstance(vif_df, pd.DataFrame)

    def test_calculate_vif_has_required_columns(self, sample_dataframe):
        """VIF DataFrame should have predictor and vif columns."""
        vif_df = calculate_vif(sample_dataframe, ['A', 'B', 'C'])
        assert 'predictor' in vif_df.columns
        assert 'vif' in vif_df.columns

    def test_calculate_vif_predictor_count(self, sample_dataframe):
        """VIF DataFrame should have one row per predictor."""
        vif_df = calculate_vif(sample_dataframe, ['A', 'B', 'C', 'D'])
        assert len(vif_df) == 4

    def test_calculate_vif_sorted_by_vif_descending(self, sample_dataframe):
        """VIF DataFrame should be sorted by VIF descending."""
        vif_df = calculate_vif(sample_dataframe, ['A', 'B', 'C'])
        assert vif_df['vif'].is_monotonic_decreasing

    def test_calculate_vif_empty_predictors_raises(self, sample_dataframe):
        """Empty predictors list should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_vif(sample_dataframe, [])

    def test_calculate_vif_missing_column_raises(self, sample_dataframe):
        """Missing column in predictors should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_vif(sample_dataframe, ['A', 'X'])

    def test_calculate_vif_constant_column_raises(self):
        """Constant column should raise ValueError."""
        df = pd.DataFrame({
            'A': [1.0] * 100,
            'B': np.random.randn(100),
        })
        with pytest.raises(ValueError):
            calculate_vif(df, ['A'])

    def test_calculate_vif_values_are_positive(self, sample_dataframe):
        """All VIF values should be positive."""
        vif_df = calculate_vif(sample_dataframe, ['A', 'B', 'C', 'D'])
        assert (vif_df['vif'] > 0).all()


class TestGetHighVifPredictors:
    """Tests for get_high_vif_predictors function."""

    @pytest.fixture
    def sample_vif_df(self):
        """Create sample VIF DataFrame."""
        return pd.DataFrame({
            'predictor': ['A', 'B', 'C', 'D'],
            'vif': [2.0, 8.5, 3.0, 12.0],
        })

    def test_get_high_vif_predictors_with_threshold(self, sample_vif_df):
        """Should return predictors above threshold."""
        high_vif = get_high_vif_predictors(sample_vif_df, threshold=5.0)
        assert set(high_vif) == {'B', 'D'}

    def test_get_high_vif_predictors_empty_result(self, sample_vif_df):
        """Should return empty list if no predictors above threshold."""
        high_vif = get_high_vif_predictors(sample_vif_df, threshold=15.0)
        assert high_vif == []

    def test_get_high_vif_predictors_all_above(self, sample_vif_df):
        """Should return all predictors if all above threshold."""
        high_vif = get_high_vif_predictors(sample_vif_df, threshold=1.0)
        assert set(high_vif) == {'A', 'B', 'C', 'D'}