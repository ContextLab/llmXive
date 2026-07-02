import pytest
import pandas as pd
import numpy as np
from code.edge_case_handler import (
    handle_edge_cases,
    check_categorical_variables,
    validate_dataset_rows,
    validate_continuous_variables,
    process_datasets_for_simulation,
    MIN_ROWS_THRESHOLD
)


class TestCategoricalDetection:
    def test_detect_object_columns(self):
        df = pd.DataFrame({
            'text_col': ['a', 'b', 'c'],
            'num_col': [1, 2, 3]
        })
        cats = check_categorical_variables(df)
        assert 'text_col' in cats
        assert 'num_col' not in cats

    def test_detect_low_cardinality_integers(self):
        # Create a large dataframe with a low cardinality integer column
        n = 1000
        df = pd.DataFrame({
            'id': range(n),
            'group': [1, 2, 3] * (n // 3)
        })
        cats = check_categorical_variables(df)
        assert 'group' in cats


class TestRowValidation:
    def test_insufficient_rows(self):
        small_df = pd.DataFrame({'a': range(10)})
        info = {'dataset_id': 'test_small', 'df': small_df}
        is_valid, reason = validate_dataset_rows(info)
        assert not is_valid
        assert 'below' in reason.lower()

    def test_sufficient_rows(self):
        large_df = pd.DataFrame({'a': range(MIN_ROWS_THRESHOLD + 10)})
        info = {'dataset_id': 'test_large', 'df': large_df}
        is_valid, reason = validate_dataset_rows(info)
        assert is_valid


class TestContinuousValidation:
    def test_no_numeric_columns(self):
        df = pd.DataFrame({
            'cat1': ['a', 'b'],
            'cat2': ['x', 'y']
        })
        info = {'dataset_id': 'test_no_num', 'df': df}
        is_valid, reason = validate_continuous_variables(info)
        assert not is_valid

    def test_has_numeric_columns(self):
        df = pd.DataFrame({
            'val': [1.0, 2.0, 3.0],
            'cat': ['a', 'b', 'c']
        })
        info = {'dataset_id': 'test_num', 'df': df}
        is_valid, reason = validate_continuous_variables(info)
        assert is_valid


class TestEdgeCaseHandler:
    def test_valid_dataset(self):
        df = pd.DataFrame({
            'val1': np.random.randn(100),
            'val2': np.random.randn(100)
        })
        info = {'dataset_id': 'valid_set', 'df': df}
        result = handle_edge_cases(info)
        
        assert result['is_valid'] is True
        assert len(result['errors']) == 0
        assert 'val1' in result['numeric_columns']

    def test_invalid_rows(self):
        df = pd.DataFrame({'val': range(5)})
        info = {'dataset_id': 'too_small', 'df': df}
        result = handle_edge_cases(info)
        
        assert result['is_valid'] is False
        assert any('rows' in err for err in result['errors'])

    def test_invalid_numeric(self):
        df = pd.DataFrame({
            'cat1': ['a', 'b'] * 50,
            'cat2': ['x', 'y'] * 50
        })
        info = {'dataset_id': 'no_nums', 'df': df}
        result = handle_edge_cases(info)
        
        assert result['is_valid'] is False
        assert any('numeric' in err for err in result['errors'])

    def test_mixed_validity(self):
        # Valid rows, but has categorical columns (should still be valid but warn)
        df = pd.DataFrame({
            'val': range(100),
            'cat': ['a', 'b'] * 50
        })
        info = {'dataset_id': 'mixed', 'df': df}
        result = handle_edge_cases(info)
        
        assert result['is_valid'] is True
        assert len(result['categorical_columns']) > 0
        assert len(result['warnings']) > 0


class TestProcessDatasets:
    def test_filter_invalid(self):
        datasets = [
            {'dataset_id': 'good', 'df': pd.DataFrame({'val': range(100)})},
            {'dataset_id': 'bad', 'df': pd.DataFrame({'val': range(5)})}
        ]
        results = process_datasets_for_simulation(datasets)
        
        # All results returned, but we check validity flags
        good_res = next(r for r in results if r['dataset_id'] == 'good')
        bad_res = next(r for r in results if r['dataset_id'] == 'bad')
        
        assert good_res['is_valid'] is True
        assert bad_res['is_valid'] is False
