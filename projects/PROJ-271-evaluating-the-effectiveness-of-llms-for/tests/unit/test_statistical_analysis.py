import pytest
import pandas as pd
import json
import os
from code.statistical_analysis import validate_merged_dataset, parse_smell_labels, merge_datasets

class TestValidateMergedDataset:
    def test_validate_with_complete_data(self):
        """Test validation with 100% complete data."""
        data = {
            'id': [1, 2, 3],
            'code': ['def a(): pass', 'def b(): pass', 'def c(): pass'],
            'loc': [10, 20, 30],
            'cyclomatic_complexity': [1, 2, 3],
            'static_smell_labels': ['["long_function"]', '["complex_function"]', '[]'],
            'semantic_vectors': ['[0.1, 0.2]', '[0.3, 0.4]', '[0.5, 0.6]'],
            'llm_labels': ['["long_function"]', '["complex_function"]', '["magic_number"]']
        }
        df = pd.DataFrame(data)
        
        is_valid, result = validate_merged_dataset(df, threshold=0.95)
        
        assert is_valid is True
        assert result['valid_rows'] == 3
        assert result['completeness_ratio'] == 1.0

    def test_validate_with_missing_data(self):
        """Test validation with some missing data."""
        data = {
            'id': [1, 2, 3, 4, 5],
            'code': ['def a(): pass', 'def b(): pass', None, 'def d(): pass', 'def e(): pass'],
            'loc': [10, 20, 30, 40, 50],
            'cyclomatic_complexity': [1, 2, 3, 4, 5],
            'static_smell_labels': ['["long_function"]', '["complex_function"]', '[]', '[]', '[]'],
            'semantic_vectors': ['[0.1, 0.2]', '[0.3, 0.4]', '[0.5, 0.6]', '[0.7, 0.8]', '[0.9, 1.0]'],
            'llm_labels': ['["long_function"]', '["complex_function"]', '[]', '[]', '[]']
        }
        df = pd.DataFrame(data)
        
        is_valid, result = validate_merged_dataset(df, threshold=0.8)
        
        # 4 out of 5 rows are valid (80%)
        assert is_valid is True
        assert result['valid_rows'] == 4
        assert result['completeness_ratio'] == 0.8

    def test_validate_fails_below_threshold(self):
        """Test validation fails when below threshold."""
        data = {
            'id': [1, 2, 3, 4, 5],
            'code': [None, None, 'def c(): pass', 'def d(): pass', 'def e(): pass'],
            'loc': [10, 20, 30, 40, 50],
            'cyclomatic_complexity': [1, 2, 3, 4, 5],
            'static_smell_labels': ['[]', '[]', '[]', '[]', '[]'],
            'semantic_vectors': ['[]', '[]', '[]', '[]', '[]'],
            'llm_labels': ['[]', '[]', '[]', '[]', '[]']
        }
        df = pd.DataFrame(data)
        
        is_valid, result = validate_merged_dataset(df, threshold=0.95)
        
        assert is_valid is False
        assert result['valid_rows'] == 3
        assert result['completeness_ratio'] == 0.6

    def test_validate_missing_columns(self):
        """Test validation fails when required columns are missing."""
        data = {
            'id': [1, 2, 3],
            'code': ['def a(): pass', 'def b(): pass', 'def c(): pass'],
            'loc': [10, 20, 30]
        }
        df = pd.DataFrame(data)
        
        is_valid, result = validate_merged_dataset(df, threshold=0.95)
        
        assert is_valid is False
        assert 'reason' in result
        assert 'Missing columns' in result['reason']

    def test_parse_smell_labels_json(self):
        """Test parsing JSON string labels."""
        labels = '["long_function", "complex_function"]'
        result = parse_smell_labels(labels)
        assert result == ["long_function", "complex_function"]

    def test_parse_smell_labels_comma_separated(self):
        """Test parsing comma-separated labels."""
        labels = "long_function, complex_function"
        result = parse_smell_labels(labels)
        assert result == ["long_function", "complex_function"]

    def test_parse_smell_labels_empty(self):
        """Test parsing empty labels."""
        labels = ""
        result = parse_smell_labels(labels)
        assert result == []

    def test_parse_smell_labels_null(self):
        """Test parsing null labels."""
        result = parse_smell_labels(None)
        assert result == []