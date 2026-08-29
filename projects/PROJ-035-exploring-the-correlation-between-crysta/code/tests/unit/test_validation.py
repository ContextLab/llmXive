"""
Unit tests for validation utilities in src/utils/validation.py.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

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
        logger = setup_logger("test_module")
        assert logger.name == "test_module"
        assert logger.level == 20  # INFO level

    def test_setup_logger_with_string_level(self):
        logger = setup_logger("test_module", level="debug")
        assert logger.level == 10  # DEBUG level

    def test_setup_logger_with_int_level(self):
        logger = setup_logger("test_module", level=logging.WARNING)
        assert logger.level == 30

    def test_setup_logger_no_duplicate_handlers(self):
        logger = setup_logger("test_module")
        num_handlers_before = len(logger.handlers)
        logger2 = setup_logger("test_module")
        num_handlers_after = len(logger2.handlers)
        assert num_handlers_before == num_handlers_after


class TestHandleError:
    @patch('sys.exit')
    def test_handle_error_exits_on_critical(self, mock_exit):
        handle_error("Test error message", "critical")
        mock_exit.assert_called_once_with(1)

    @patch('sys.exit')
    def test_handle_error_exits_on_error(self, mock_exit):
        handle_error("Test error message", "error")
        mock_exit.assert_called_once_with(1)

    @patch('sys.exit')
    def test_handle_error_warning_no_exit(self, mock_exit):
        handle_error("Test warning", "warning")
        mock_exit.assert_not_called()


class TestCalculateVif:
    def test_calculate_vif_basic(self):
        # Create data with known multicollinearity
        np.random.seed(42)
        df = pd.DataFrame({
            'x1': np.random.randn(100),
            'x2': np.random.randn(100),
            'x3': np.random.randn(100)
        })

        vif_df = calculate_vif(df, ['x1', 'x2', 'x3'])

        assert len(vif_df) == 3
        assert 'feature' in vif_df.columns
        assert 'vif' in vif_df.columns
        assert all(vif_df['vif'] >= 1.0)  # VIF >= 1 always

    def test_calculate_vif_with_collinearity(self):
        # Create data with high multicollinearity
        np.random.seed(42)
        x = np.random.randn(100)
        df = pd.DataFrame({
            'x1': x,
            'x2': x * 2 + np.random.randn(100) * 0.1,  # Highly correlated
            'x3': np.random.randn(100)
        })

        vif_df = calculate_vif(df, ['x1', 'x2', 'x3'])

        # x1 and x2 should have high VIF
        x1_vif = vif_df[vif_df['feature'] == 'x1']['vif'].values[0]
        x2_vif = vif_df[vif_df['feature'] == 'x2']['vif'].values[0]
        assert x1_vif > 5.0 or x2_vif > 5.0, "Expected high VIF for correlated variables"

    def test_calculate_vif_missing_predictor(self):
        df = pd.DataFrame({'x1': [1, 2, 3]})
        with pytest.raises(SystemExit):
            calculate_vif(df, ['x1', 'x2'])

    def test_calculate_vif_empty_predictors(self):
        df = pd.DataFrame({'x1': [1, 2, 3]})
        with pytest.raises(SystemExit):
            calculate_vif(df, [])


class TestGetHighVifPredictors:
    def test_get_high_vif_predictors_basic(self):
        vif_df = pd.DataFrame({
            'feature': ['x1', 'x2', 'x3'],
            'vif': [2.0, 6.5, 8.0]
        })

        high_vif = get_high_vif_predictors(vif_df, threshold=5.0)
        assert set(high_vif) == {'x2', 'x3'}

    def test_get_high_vif_predictors_empty(self):
        vif_df = pd.DataFrame({
            'feature': ['x1', 'x2'],
            'vif': [2.0, 3.0]
        })

        high_vif = get_high_vif_predictors(vif_df, threshold=5.0)
        assert high_vif == []

    def test_get_high_vif_predictors_empty_df(self):
        vif_df = pd.DataFrame(columns=['feature', 'vif'])
        high_vif = get_high_vif_predictors(vif_df, threshold=5.0)
        assert high_vif == []


class TestScanCausalLanguage:
    def test_scan_causal_language_no_matches(self):
        text = "The temperature is correlated with thermal conductivity."
        result = scan_causal_language(text)

        assert result['found'] is False
        assert result['count'] == 0
        assert result['matches'] == []

    def test_scan_causal_language_with_matches(self):
        text = "The structure causes increased conductivity. This leads to better performance."
        result = scan_causal_language(text)

        assert result['found'] is True
        assert result['count'] >= 2
        assert any(m['keyword'] == 'cause' for m in result['matches'])
        assert any(m['keyword'] == 'leads to' for m in result['matches'])

    def test_scan_causal_language_case_insensitive(self):
        text = "CAUSES and Causes and causes are all detected."
        result = scan_causal_language(text)

        assert result['found'] is True
        assert result['count'] >= 3

    def test_scan_causal_language_context_extraction(self):
        text = "The crystal structure causes higher thermal conductivity values."
        result = scan_causal_language(text)

        assert result['found'] is True
        assert len(result['matches']) > 0
        assert 'context' in result['matches'][0]
        assert 'crystal' in result['matches'][0]['context'].lower()


class TestValidateCausalLanguage:
    def test_validate_causal_language_pass(self):
        text = "The temperature is associated with thermal conductivity."
        assert validate_causal_language(text, fail_on_match=False) is True

    def test_validate_causal_language_fail(self):
        text = "The structure causes increased conductivity."
        assert validate_causal_language(text, fail_on_match=False) is False

    @patch('sys.exit')
    def test_validate_causal_language_fail_exits(self, mock_exit):
        text = "The structure causes increased conductivity."
        validate_causal_language(text, fail_on_match=True)
        mock_exit.assert_called_once_with(1)


class TestValidateDataFrameColumns:
    def test_validate_columns_all_present(self):
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})
        missing = validate_dataframe_columns(df, ['a', 'b', 'c'])
        assert missing == []

    def test_validate_columns_some_missing(self):
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        missing = validate_dataframe_columns(df, ['a', 'b', 'c'])
        assert missing == ['c']

    def test_validate_columns_all_missing(self):
        df = pd.DataFrame({'a': [1, 2]})
        missing = validate_dataframe_columns(df, ['b', 'c'])
        assert set(missing) == {'b', 'c'}


class TestValidateNoNulls:
    def test_validate_no_nulls_clean_data(self):
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        nulls = validate_no_nulls(df)
        assert nulls == {}

    def test_validate_no_nulls_with_nulls(self):
        df = pd.DataFrame({'a': [1, np.nan, 3], 'b': [4, 5, np.nan]})
        nulls = validate_no_nulls(df)
        assert nulls == {'a': 1, 'b': 1}

    def test_validate_no_nulls_specific_columns(self):
        df = pd.DataFrame({'a': [1, np.nan, 3], 'b': [4, 5, 6], 'c': [7, 8, np.nan]})
        nulls = validate_no_nulls(df, columns=['a', 'b'])
        assert nulls == {'a': 1}
        assert 'c' not in nulls


class TestValidateDataTypes:
    def test_validate_types_all_match(self):
        df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [1.0, 2.0, 3.0],
            'c': ['x', 'y', 'z']
        })
        mismatches = validate_data_types(df, {'a': 'int', 'b': 'float', 'c': 'object'})
        assert mismatches == []

    def test_validate_types_mismatch(self):
        df = pd.DataFrame({
            'a': [1.0, 2.0, 3.0],
            'b': [1, 2, 3]
        })
        mismatches = validate_data_types(df, {'a': 'int', 'b': 'float'})
        assert len(mismatches) == 2

    def test_validate_types_missing_column(self):
        df = pd.DataFrame({'a': [1, 2, 3]})
        mismatches = validate_data_types(df, {'a': 'int', 'b': 'float'})
        assert 'b: column missing' in mismatches