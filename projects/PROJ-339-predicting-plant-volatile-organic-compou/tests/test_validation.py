"""
Unit tests for code/utils/validation.py (Task T006).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.validation import (
    check_replicates,
    validate_data_types,
    validate_environmental_metadata,
    generate_validation_report
)


class TestCheckReplicates:
    def test_all_groups_satisfy_min_count(self):
        data = {
            'condition': ['A', 'A', 'A', 'B', 'B', 'B'],
            'value': [1, 2, 3, 4, 5, 6]
        }
        df = pd.DataFrame(data)
        valid, failing = check_replicates(df, 'condition', min_count=3)
        assert valid is True
        assert failing == []

    def test_some_groups_below_min_count(self):
        data = {
            'condition': ['A', 'A', 'A', 'B', 'B', 'C'],
            'value': [1, 2, 3, 4, 5, 6]
        }
        df = pd.DataFrame(data)
        valid, failing = check_replicates(df, 'condition', min_count=3)
        assert valid is False
        assert set(failing) == {'B', 'C'}

    def test_missing_group_column(self):
        data = {'value': [1, 2, 3]}
        df = pd.DataFrame(data)
        with pytest.raises(ValueError, match="Group column"):
            check_replicates(df, 'non_existent_col')


class TestValidateDataTypes:
    def test_all_numeric_valid(self):
        data = {
            'num1': [1, 2, 3],
            'num2': [1.1, 2.2, 3.3]
        }
        df = pd.DataFrame(data)
        valid, details = validate_data_types(df)
        assert valid is True
        assert details['errors'] == []

    def test_object_column_with_numeric_strings(self):
        # This should pass if pd.to_numeric can convert it, but our logic
        # uses errors='raise'. If the whole column is convertible, it passes.
        # However, if there's a mix or non-numeric, it fails.
        data = {
            'num_str': ['1', '2', '3'],
            'val': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        # 'num_str' is object. pd.to_numeric(['1','2','3']) works.
        # So it should be valid.
        valid, details = validate_data_types(df)
        assert valid is True

    def test_object_column_with_non_numeric(self):
        data = {
            'mixed': ['1', '2', 'abc'],
            'val': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        valid, details = validate_data_types(df)
        assert valid is False
        assert any('mixed' in err for err in details['errors'])

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        valid, details = validate_data_types(df)
        assert valid is True


class TestValidateEnvironmentalMetadata:
    def test_all_required_present_and_valid(self):
        data = {
            'temp': [20.0, 21.0],
            'light': [100, 110],
            'co2': [400, 410]
        }
        df = pd.DataFrame(data)
        valid, issues = validate_environmental_metadata(df, ['temp', 'light', 'co2'])
        assert valid is True
        assert issues == []

    def test_missing_column(self):
        data = {'temp': [20.0]}
        df = pd.DataFrame(data)
        valid, issues = validate_environmental_metadata(df, ['temp', 'light'])
        assert valid is False
        assert any('Missing required column' in i for i in issues)

    def test_null_values_in_required_column(self):
        data = {
            'temp': [20.0, np.nan],
            'light': [100, 110]
        }
        df = pd.DataFrame(data)
        valid, issues = validate_environmental_metadata(df, ['temp', 'light'])
        assert valid is False
        assert any('null' in i.lower() for i in issues)


class TestGenerateValidationReport:
    def test_report_structure(self):
        data = {'a': [1, 2], 'b': ['x', 'y']}
        df = pd.DataFrame(data)
        report = generate_validation_report(df)
        
        assert 'valid' in report
        assert 'row_count' in report
        assert 'column_count' in report
        assert 'errors' in report
        assert report['row_count'] == 2
        assert report['column_count'] == 2

    def test_report_catches_errors(self):
        data = {'bad': ['a', 'b', 'c'], 'good': [1, 2, 3]}
        df = pd.DataFrame(data)
        report = generate_validation_report(df)
        assert report['valid'] is False
        assert len(report['errors']) > 0