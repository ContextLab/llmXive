"""
Tests for code/utils/validation.py
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from pathlib import Path

from code.utils.validation import (
    check_replicates,
    validate_data_types,
    validate_environmental_metadata,
    generate_validation_report,
    _infer_type,
    _types_match
)


class TestInferType:
    def test_float_inference(self):
        s = pd.Series([1.1, 2.2, 3.3])
        assert _infer_type(s) == 'numeric'

    def test_int_inference(self):
        s = pd.Series([1, 2, 3])
        assert _infer_type(s) == 'integer'

    def test_string_inference(self):
        s = pd.Series(['a', 'b', 'c'])
        assert _infer_type(s) == 'string'

    def test_bool_inference(self):
        s = pd.Series([True, False, True])
        assert _infer_type(s) == 'boolean'

    def test_category_inference(self):
        s = pd.Series(['a', 'b', 'c'], dtype='category')
        assert _infer_type(s) == 'category'


class TestTypesMatch:
    def test_exact_match(self):
        assert _types_match('numeric', 'numeric') is True
        assert _types_match('string', 'string') is True

    def test_int_as_numeric(self):
        assert _types_match('integer', 'numeric') is True

    def test_mismatch(self):
        assert _types_match('string', 'numeric') is False
        assert _types_match('boolean', 'integer') is False


class TestCheckReplicates:
    def test_insufficient_replicates_removed(self):
        df = pd.DataFrame({
            'condition': ['A', 'A', 'B', 'B', 'B', 'C'],
            'value': [1, 2, 3, 4, 5, 6]
        })
        filtered, report = check_replicates(df, ['condition'], min_replicates=3)
        
        assert 'C' not in filtered['condition'].values
        assert 'A' not in filtered['condition'].values
        assert len(filtered) == 3
        assert report['conditions_with_insufficient_replicates'] == 2
        assert report['samples_removed'] == 3

    def test_all_pass(self):
        df = pd.DataFrame({
            'condition': ['A', 'A', 'A', 'B', 'B', 'B'],
            'value': [1, 2, 3, 4, 5, 6]
        })
        filtered, report = check_replicates(df, ['condition'], min_replicates=3)
        
        assert len(filtered) == 6
        assert report['conditions_with_insufficient_replicates'] == 0

    def test_missing_columns_raises(self):
        df = pd.DataFrame({'a': [1, 2, 3]})
        with pytest.raises(ValueError):
            check_replicates(df, ['nonexistent'], min_replicates=2)


class TestValidateDataTypes:
    def test_valid_types(self):
        df = pd.DataFrame({
            'num': [1.1, 2.2],
            'int_col': [1, 2],
            'str_col': ['a', 'b']
        })
        expected = {
            'num': 'numeric',
            'int_col': 'integer',
            'str_col': 'string'
        }
        is_valid, report = validate_data_types(df, expected)
        
        assert is_valid is True
        assert report['mismatched_columns'] == 0

    def test_mismatched_types(self):
        df = pd.DataFrame({
            'num': [1, 2],  # int, expected numeric (should pass)
            'str_as_num': ['a', 'b']  # string, expected numeric (fail)
        })
        expected = {
            'num': 'numeric',
            'str_as_num': 'numeric'
        }
        is_valid, report = validate_data_types(df, expected)
        
        assert is_valid is False
        assert report['mismatched_columns'] == 1
        assert report['details'][0]['column'] == 'str_as_num'

    def test_missing_column(self):
        df = pd.DataFrame({'a': [1, 2]})
        expected = {'a': 'numeric', 'missing': 'string'}
        is_valid, report = validate_data_types(df, expected)
        
        assert is_valid is False
        assert report['mismatched_columns'] == 1
        assert report['details'][0]['issue'] == 'missing_column'


class TestValidateEnvironmentalMetadata:
    def test_missing_columns(self):
        df = pd.DataFrame({'a': [1, 2, 3]})
        is_valid, report = validate_environmental_metadata(
            df,
            required_columns=['temp', 'light'],
            continuous_columns=['temp']
        )
        
        assert is_valid is False
        assert len(report['issues']) == 1
        assert report['issues'][0]['type'] == 'missing_columns'

    def test_nan_in_continuous(self):
        df = pd.DataFrame({
            'temp': [1.0, np.nan, 3.0],
            'light': [100, 200, 300]
        })
        is_valid, report = validate_environmental_metadata(
            df,
            required_columns=['temp', 'light'],
            continuous_columns=['temp']
        )
        
        assert is_valid is False
        assert len(report['issues']) == 1
        assert report['issues'][0]['type'] == 'missing_continuous_values'
        assert report['issues'][0]['details'][0]['nan_count'] == 1

    def test_valid_metadata(self):
        df = pd.DataFrame({
            'temp': [1.0, 2.0, 3.0],
            'light': [100, 200, 300]
        })
        is_valid, report = validate_environmental_metadata(
            df,
            required_columns=['temp', 'light'],
            continuous_columns=['temp', 'light']
        )
        
        assert is_valid is True


class TestGenerateValidationReport:
    def test_full_report_generation(self):
        df = pd.DataFrame({
            'condition': ['A', 'A', 'A', 'B', 'B'],  # B has only 2, should be removed
            'temp': [1.0, 2.0, 3.0, 4.0, 5.0],
            'light': [100, 200, 300, 400, 500],
            'value': [1, 2, 3, 4, 5]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'report.json')
            
            report = generate_validation_report(
                df,
                output_path,
                replicate_config={'condition_columns': ['condition'], 'min_replicates': 3},
                type_config={'temp': 'numeric', 'light': 'numeric', 'value': 'integer'},
                env_config={
                    'required_columns': ['temp', 'light'],
                    'continuous_columns': ['temp', 'light']
                }
            )
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
            
            assert saved_report['checks']['replicates']['conditions_with_insufficient_replicates'] == 1
            assert saved_report['checks']['replicates']['samples_removed'] == 2
            assert saved_report['rows_after_replicate_filter'] == 3
            assert saved_report['checks']['data_types']['is_valid'] is True
            assert saved_report['checks']['environmental_metadata']['is_valid'] is True