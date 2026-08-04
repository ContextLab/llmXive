"""
Unit tests for the validation script (T025).
Verifies that the validation logic correctly identifies missing metrics.
"""
import os
import sys
import csv
import json
import tempfile
from pathlib import Path
import pytest

# Add code/scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code' / 'scripts'))

from validate_features import (
    validate_columns_present,
    validate_no_missing_metrics,
    REQUIRED_COLUMNS,
    METRIC_COLUMNS
)

class TestValidateColumnsPresent:
    def test_all_columns_present(self):
        """Test that no missing columns are reported when all are present."""
        rows = [{col: 'value' for col in REQUIRED_COLUMNS}]
        missing = validate_columns_present(rows)
        assert missing == set()

    def test_missing_columns_reported(self):
        """Test that missing columns are correctly identified."""
        rows = [{'task_id': '1', 'code_diff': 'diff'}]  # Missing most columns
        missing = validate_columns_present(rows)
        assert 'dependency_depth' in missing
        assert 'cyclomatic_complexity' in missing

    def test_empty_rows(self):
        """Test behavior with empty rows list."""
        missing = validate_columns_present([])
        assert missing == set()

class TestValidateNoMissingMetrics:
    def test_all_metrics_present(self):
        """Test that no issues reported when all metrics present."""
        rows = [{
            'task_id': '1',
            'dependency_depth': '3',
            'cyclomatic_complexity': '5',
            'semantic_complexity_score': '2.5',
            'lines_of_code': '150'
        }]
        issues = validate_no_missing_metrics(rows)
        assert len(issues) == 0

    def test_none_values_detected(self):
        """Test that None values are detected as missing."""
        rows = [{
            'task_id': '1',
            'dependency_depth': None,
            'cyclomatic_complexity': '5',
            'semantic_complexity_score': '2.5',
            'lines_of_code': '150'
        }]
        issues = validate_no_missing_metrics(rows)
        assert len(issues) == 1
        assert issues[0]['missing_column'] == 'dependency_depth'

    def test_empty_string_detected(self):
        """Test that empty strings are detected as missing."""
        rows = [{
            'task_id': '1',
            'dependency_depth': '',
            'cyclomatic_complexity': '5',
            'semantic_complexity_score': '2.5',
            'lines_of_code': '150'
        }]
        issues = validate_no_missing_metrics(rows)
        assert len(issues) == 1
        assert issues[0]['missing_column'] == 'dependency_depth'

    def test_whitespace_only_detected(self):
        """Test that whitespace-only strings are detected as missing."""
        rows = [{
            'task_id': '1',
            'dependency_depth': '   ',
            'cyclomatic_complexity': '5',
            'semantic_complexity_score': '2.5',
            'lines_of_code': '150'
        }]
        issues = validate_no_missing_metrics(rows)
        assert len(issues) == 1
        assert issues[0]['missing_column'] == 'dependency_depth'

    def test_non_numeric_detected(self):
        """Test that non-numeric values are detected in numeric columns."""
        rows = [{
            'task_id': '1',
            'dependency_depth': 'abc',
            'cyclomatic_complexity': '5',
            'semantic_complexity_score': '2.5',
            'lines_of_code': '150'
        }]
        issues = validate_no_missing_metrics(rows)
        assert len(issues) == 1
        assert issues[0]['missing_column'] == 'dependency_depth'
        assert issues[0].get('issue') == 'non-numeric'

    def test_multiple_issues_reported(self):
        """Test that multiple missing metrics in one row are all reported."""
        rows = [{
            'task_id': '1',
            'dependency_depth': None,
            'cyclomatic_complexity': '',
            'semantic_complexity_score': '2.5',
            'lines_of_code': '150'
        }]
        issues = validate_no_missing_metrics(rows)
        assert len(issues) == 2
        cols = [i['missing_column'] for i in issues]
        assert 'dependency_depth' in cols
        assert 'cyclomatic_complexity' in cols

    def test_multiple_rows_validated(self):
        """Test validation across multiple rows."""
        rows = [
            {
                'task_id': '1',
                'dependency_depth': '3',
                'cyclomatic_complexity': '5',
                'semantic_complexity_score': '2.5',
                'lines_of_code': '150'
            },
            {
                'task_id': '2',
                'dependency_depth': None,
                'cyclomatic_complexity': '5',
                'semantic_complexity_score': '2.5',
                'lines_of_code': '150'
            },
            {
                'task_id': '3',
                'dependency_depth': '4',
                'cyclomatic_complexity': '',
                'semantic_complexity_score': '2.5',
                'lines_of_code': '150'
            }
        ]
        issues = validate_no_missing_metrics(rows)
        assert len(issues) == 2
        assert issues[0]['task_id'] == '2'
        assert issues[1]['task_id'] == '3'

class TestIntegration:
    def test_valid_features_file(self, tmp_path):
        """Test validation with a properly formatted features.csv."""
        features_path = tmp_path / 'features.csv'
        with open(features_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                'task_id': '1',
                'code_diff': 'diff',
                'dynamic_execution_outcome': 'Pass',
                'dependency_depth': '3',
                'cyclomatic_complexity': '5',
                'semantic_complexity_score': '2.5',
                'lines_of_code': '150'
            })
        
        # Import and run validation logic
        from validate_features import load_features_csv, validate_no_missing_metrics
        rows = load_features_csv(features_path)
        issues = validate_no_missing_metrics(rows)
        assert len(issues) == 0

    def test_invalid_features_file(self, tmp_path):
        """Test validation with a features.csv containing missing values."""
        features_path = tmp_path / 'features.csv'
        with open(features_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                'task_id': '1',
                'code_diff': 'diff',
                'dynamic_execution_outcome': 'Pass',
                'dependency_depth': '',
                'cyclomatic_complexity': '5',
                'semantic_complexity_score': '2.5',
                'lines_of_code': '150'
            })
        
        from validate_features import load_features_csv, validate_no_missing_metrics
        rows = load_features_csv(features_path)
        issues = validate_no_missing_metrics(rows)
        assert len(issues) == 1
        assert issues[0]['missing_column'] == 'dependency_depth'
