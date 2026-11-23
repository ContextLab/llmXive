"""
Unit tests for validation utilities in src/utils/validation.py
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
import sys
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.utils.validation import (
    setup_logger,
    handle_error,
    calculate_vif,
    get_high_vif_predictors,
    scan_causal_language,
    validate_causal_language,
    validate_dataframe_columns,
    validate_no_nulls,
    validate_data_types
)


class TestSetupLogger:
    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a logger instance"""
        logger = setup_logger('test_logger')
        assert logger is not None
        assert logger.name == 'test_logger'

    def test_setup_logger_with_info_level(self):
        """Test logger is configured with INFO level"""
        logger = setup_logger('test_logger_info', level='INFO')
        assert logger.level == 20  # logging.INFO

    def test_setup_logger_with_debug_level(self):
        """Test logger is configured with DEBUG level"""
        logger = setup_logger('test_logger_debug', level='DEBUG')
        assert logger.level == 10  # logging.DEBUG

    def test_setup_logger_no_duplicate_handlers(self):
        """Test that calling setup_logger twice doesn't add duplicate handlers"""
        logger = setup_logger('test_logger_dup')
        initial_handler_count = len(logger.handlers)
        logger = setup_logger('test_logger_dup')
        assert len(logger.handlers) == initial_handler_count


class TestHandleError:
    def test_handle_error_info_level(self):
        """Test handle_error with INFO level doesn't exit"""
        with patch('sys.exit') as mock_exit:
            handle_error("Test info message", level='info')
            mock_exit.assert_not_called()

    def test_handle_error_critical_level(self):
        """Test handle_error with CRITICAL level exits"""
        with pytest.raises(SystemExit):
            handle_error("Test critical message", level='critical')

    def test_handle_error_warning_level(self):
        """Test handle_error with WARNING level doesn't exit"""
        with patch('sys.exit') as mock_exit:
            handle_error("Test warning message", level='warning')
            mock_exit.assert_not_called()


class TestCalculateVif:
    def test_calculate_vif_basic(self):
        """Test VIF calculation with simple data"""
        df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [2, 4, 6, 8, 10],
            'C': [1, 3, 5, 7, 9]
        })
        vif_df = calculate_vif(df, ['A', 'B', 'C'])

        assert 'predictor' in vif_df.columns
        assert 'vif' in vif_df.columns
        assert len(vif_df) == 3

    def test_calculate_vif_missing_column(self):
        """Test VIF calculation raises error for missing column"""
        df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [2, 4, 6, 8, 10]
        })
        with pytest.raises(ValueError):
            calculate_vif(df, ['A', 'B', 'C'])

    def test_calculate_vif_with_nan(self):
        """Test VIF calculation handles NaN values"""
        df = pd.DataFrame({
            'A': [1, 2, np.nan, 4, 5],
            'B': [2, 4, 6, 8, 10],
            'C': [1, 3, 5, 7, 9]
        })
        # Should not raise, just drop NaN rows
        vif_df = calculate_vif(df, ['A', 'B', 'C'])
        assert len(vif_df) == 3

    def test_calculate_vif_all_nan(self):
        """Test VIF calculation raises error when all data is NaN"""
        df = pd.DataFrame({
            'A': [np.nan, np.nan, np.nan],
            'B': [np.nan, np.nan, np.nan]
        })
        with pytest.raises(ValueError):
            calculate_vif(df, ['A', 'B'])


class TestGetHighVifPredictors:
    def test_get_high_vif_predictors_below_threshold(self):
        """Test that predictors below threshold are not returned"""
        df = pd.DataFrame({
            'A': np.random.rand(100),
            'B': np.random.rand(100),
            'C': np.random.rand(100)
        })
        high_vif = get_high_vif_predictors(df, ['A', 'B', 'C'], threshold=5.0)
        # With random data, VIF should be low
        assert len(high_vif) == 0

    def test_get_high_vif_predictors_with_correlation(self):
        """Test detection of high VIF with correlated variables"""
        # Create highly correlated variables
        base = np.random.rand(100)
        df = pd.DataFrame({
            'A': base,
            'B': base * 2 + 0.1 * np.random.rand(100),  # Highly correlated with A
            'C': np.random.rand(100)
        })
        high_vif = get_high_vif_predictors(df, ['A', 'B', 'C'], threshold=5.0)
        # At least one of A or B should have high VIF
        assert len(high_vif) > 0


class TestScanCausalLanguage:
    def test_scan_causal_language_no_matches(self):
        """Test scan with no prohibited language"""
        text = "The temperature is correlated with conductivity."
        result = scan_causal_language(text)
        assert result['found'] is False
        assert result['count'] == 0
        assert len(result['matches']) == 0

    def test_scan_causal_language_with_cause(self):
        """Test scan detects 'cause'"""
        text = "Temperature causes changes in conductivity."
        result = scan_causal_language(text)
        assert result['found'] is True
        assert result['count'] >= 1
        assert any('cause' in match['phrase'] for match in result['matches'])

    def test_scan_causal_language_with_leads_to(self):
        """Test scan detects 'leads to'"""
        text = "Higher temperatures lead to increased conductivity."
        result = scan_causal_language(text)
        assert result['found'] is True
        assert result['count'] >= 1

    def test_scan_causal_language_with_driven_by(self):
        """Test scan detects 'driven by'"""
        text = "The effect is driven by structural distortions."
        result = scan_causal_language(text)
        assert result['found'] is True
        assert result['count'] >= 1

    def test_scan_causal_language_with_effect_of(self):
        """Test scan detects 'effect of'"""
        text = "We studied the effect of temperature on conductivity."
        result = scan_causal_language(text)
        assert result['found'] is True
        assert result['count'] >= 1

    def test_scan_causal_language_with_result_of(self):
        """Test scan detects 'result of'"""
        text = "The change is a result of crystal structure."
        result = scan_causal_language(text)
        assert result['found'] is True
        assert result['count'] >= 1

    def test_scan_causal_language_with_induces(self):
        """Test scan detects 'induces'"""
        text = "Doping induces changes in thermal properties."
        result = scan_causal_language(text)
        assert result['found'] is True
        assert result['count'] >= 1

    def test_scan_causal_language_with_triggers(self):
        """Test scan detects 'triggers'"""
        text = "The phase transition triggers conductivity changes."
        result = scan_causal_language(text)
        assert result['found'] is True
        assert result['count'] >= 1

    def test_scan_causal_language_multiple_matches(self):
        """Test scan detects multiple prohibited phrases"""
        text = "Temperature causes changes and leads to effects."
        result = scan_causal_language(text)
        assert result['found'] is True
        assert result['count'] >= 2


class TestValidateCausalLanguage:
    def test_validate_causal_language_pass(self):
        """Test validation passes with no violations"""
        text = "Temperature is associated with conductivity changes."
        result = validate_causal_language(text, fail_on_found=False)
        assert result is True

    def test_validate_causal_language_fail(self):
        """Test validation fails with violations"""
        text = "Temperature causes conductivity changes."
        result = validate_causal_language(text, fail_on_found=False)
        assert result is False

    def test_validate_causal_language_critical_exit(self):
        """Test validation exits on critical violation"""
        text = "Temperature causes conductivity changes."
        with pytest.raises(SystemExit):
            validate_causal_language(text, fail_on_found=True)


class TestValidateDataFrameColumns:
    def test_validate_dataframe_columns_all_present(self):
        """Test validation passes when all columns present"""
        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4], 'C': [5, 6]})
        result = validate_dataframe_columns(df, ['A', 'B'])
        assert result is True

    def test_validate_dataframe_columns_missing(self):
        """Test validation fails when columns missing"""
        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        result = validate_dataframe_columns(df, ['A', 'B', 'C'])
        assert result is False


class TestValidateNoNulls:
    def test_validate_no_nulls_all_valid(self):
        """Test validation passes with no nulls"""
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        result = validate_no_nulls(df)
        assert result is True

    def test_validate_no_nulls_with_nulls(self):
        """Test validation fails with nulls"""
        df = pd.DataFrame({'A': [1, np.nan, 3], 'B': [4, 5, 6]})
        result = validate_no_nulls(df)
        assert result is False

    def test_validate_no_nulls_specific_columns(self):
        """Test validation on specific columns"""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, np.nan, 6],
            'C': [7, 8, 9]
        })
        result = validate_no_nulls(df, columns=['A', 'C'])
        assert result is True

        result = validate_no_nulls(df, columns=['A', 'B'])
        assert result is False


class TestValidateDataTypes:
    def test_validate_data_types_correct(self):
        """Test validation passes with correct types"""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [1.0, 2.0, 3.0],
            'C': ['x', 'y', 'z']
        })
        result = validate_data_types(df, {
            'A': np.integer,
            'B': np.floating,
            'C': np.str_
        })
        assert result is True

    def test_validate_data_types_incorrect(self):
        """Test validation fails with incorrect types"""
        df = pd.DataFrame({
            'A': [1.0, 2.0, 3.0],  # Float instead of int
            'B': [1.0, 2.0, 3.0]
        })
        result = validate_data_types(df, {
            'A': np.integer,
            'B': np.floating
        })
        assert result is False

    def test_validate_data_types_missing_column(self):
        """Test validation fails for missing column"""
        df = pd.DataFrame({'A': [1, 2, 3]})
        result = validate_data_types(df, {'A': np.integer, 'B': np.floating})
        assert result is False