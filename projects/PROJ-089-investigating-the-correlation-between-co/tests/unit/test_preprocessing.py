"""
Unit tests for preprocessing.py module (T015).

Tests:
- is_source_file: Correct identification of source vs non-source files
- filter_non_source_files: Proper filtering of non-source files
- apply_loc_threshold: Correct filtering by avg_loc threshold
- generate_parameterized_datasets: Generation of multiple threshold datasets
- validate_raw_metrics: Validation of required columns and non-null values
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocessing import (
    is_source_file,
    filter_non_source_files,
    apply_loc_threshold,
    generate_parameterized_datasets,
    validate_raw_metrics,
    EXCLUDED_DIRS,
    EXCLUDED_FILES,
    SOURCE_EXTENSIONS
)

class TestIsSourceFile:
    """Tests for is_source_file function."""
    
    def test_python_file(self):
        """Python files should be considered source files."""
        assert is_source_file(Path('main.py')) is True
        assert is_source_file(Path('src/utils.py')) is True
        assert is_source_file(Path('lib/core/module.py')) is True
    
    def test_javascript_file(self):
        """JavaScript files should be considered source files."""
        assert is_source_file(Path('app.js')) is True
        assert is_source_file(Path('src/index.ts')) is True
    
    def test_java_file(self):
        """Java files should be considered source files."""
        assert is_source_file(Path('Main.java')) is True
        assert is_source_file(Path('src/com/example/App.java')) is True
    
    def test_go_file(self):
        """Go files should be considered source files."""
        assert is_source_file(Path('main.go')) is True
        assert is_source_file(Path('cmd/server/main.go')) is True
    
    def test_rust_file(self):
        """Rust files should be considered source files."""
        assert is_source_file(Path('lib.rs')) is True
        assert is_source_file(Path('src/main.rs')) is True
    
    def test_non_source_extension(self):
        """Files with non-source extensions should be excluded."""
        assert is_source_file(Path('README.md')) is False
        assert is_source_file(Path('data.csv')) is False
        assert is_source_file(Path('config.json')) is False
        assert is_source_file(Path('image.png')) is False
    
    def test_excluded_directory(self):
        """Files in excluded directories should be excluded."""
        assert is_source_file(Path('node_modules/package/index.js')) is False
        assert is_source_file(Path('venv/lib/python3.9/site-packages/module.py')) is False
        assert is_source_file(Path('.git/config')) is False
        assert is_source_file(Path('__pycache__/module.cpython-39.pyc')) is False
    
    def test_excluded_file(self):
        """Specific excluded files should be excluded even with source extension."""
        assert is_source_file(Path('package-lock.json')) is False
        assert is_source_file(Path('requirements.txt')) is False
        assert is_source_file(Path('Dockerfile')) is False
        assert is_source_file(Path('Makefile')) is False
    
    def test_nested_excluded_directory(self):
        """Files in nested excluded directories should be excluded."""
        assert is_source_file(Path('src/node_modules/deep/index.js')) is False
        assert is_source_file(Path('project/.git/objects/abc123')) is False

class TestFilterNonSourceFiles:
    """Tests for filter_non_source_files function."""
    
    def test_filter_mixed_files(self):
        """Should filter out non-source files from a mixed dataframe."""
        df = pd.DataFrame({
            'file_path': [
                'main.py',
                'README.md',
                'src/utils.js',
                'data.csv',
                'lib/core/module.go',
                'package-lock.json',
                'node_modules/pkg/index.js'
            ],
            'total_lines_changed': [100, 50, 200, 30, 150, 10, 5],
            'debt_score': [5, 2, 10, 1, 8, 1, 0],
            'avg_loc': [15, 10, 20, 5, 25, 8, 3],
            'contributor_count': [3, 1, 5, 2, 4, 1, 1]
        })
        
        filtered = filter_non_source_files(df)
        
        # Should keep: main.py, src/utils.js, lib/core/module.go
        # Should remove: README.md, data.csv, package-lock.json, node_modules/pkg/index.js
        assert len(filtered) == 3
        assert 'README.md' not in filtered['file_path'].values
        assert 'data.csv' not in filtered['file_path'].values
        assert 'package-lock.json' not in filtered['file_path'].values
        assert 'node_modules/pkg/index.js' not in filtered['file_path'].values
    
    def test_empty_dataframe(self):
        """Should handle empty dataframes gracefully."""
        df = pd.DataFrame(columns=['file_path', 'total_lines_changed', 'debt_score', 'avg_loc', 'contributor_count'])
        filtered = filter_non_source_files(df)
        assert len(filtered) == 0
    
    def test_all_source_files(self):
        """Should keep all files if all are source files."""
        df = pd.DataFrame({
            'file_path': ['main.py', 'utils.js', 'core.go'],
            'total_lines_changed': [10, 20, 30],
            'debt_score': [1, 2, 3],
            'avg_loc': [15, 20, 25],
            'contributor_count': [1, 2, 3]
        })
        
        filtered = filter_non_source_files(df)
        assert len(filtered) == 3

class TestApplyLocThreshold:
    """Tests for apply_loc_threshold function."""
    
    def test_threshold_filtering(self):
        """Should filter files based on avg_loc threshold."""
        df = pd.DataFrame({
            'file_path': ['a.py', 'b.py', 'c.py', 'd.py'],
            'avg_loc': [5, 10, 15, 20],
            'total_lines_changed': [10, 20, 30, 40],
            'debt_score': [1, 2, 3, 4],
            'contributor_count': [1, 1, 1, 1]
        })
        
        filtered = apply_loc_threshold(df, threshold=10)
        
        assert len(filtered) == 3
        assert all(filtered['avg_loc'] >= 10)
        assert 5 not in filtered['avg_loc'].values
    
    def test_threshold_zero(self):
        """Threshold of 0 should keep all files."""
        df = pd.DataFrame({
            'file_path': ['a.py', 'b.py'],
            'avg_loc': [0, 5],
            'total_lines_changed': [10, 20],
            'debt_score': [1, 2],
            'contributor_count': [1, 1]
        })
        
        filtered = apply_loc_threshold(df, threshold=0)
        assert len(filtered) == 2
    
    def test_threshold_all_excluded(self):
        """High threshold should exclude all files."""
        df = pd.DataFrame({
            'file_path': ['a.py', 'b.py'],
            'avg_loc': [5, 10],
            'total_lines_changed': [10, 20],
            'debt_score': [1, 2],
            'contributor_count': [1, 1]
        })
        
        filtered = apply_loc_threshold(df, threshold=100)
        assert len(filtered) == 0
    
    def test_missing_column(self):
        """Should raise error if required column is missing."""
        df = pd.DataFrame({
            'file_path': ['a.py'],
            'total_lines_changed': [10]
        })
        
        with pytest.raises(ValueError, match="Column 'avg_loc' not found"):
            apply_loc_threshold(df, threshold=10)

class TestGenerateParameterizedDatasets:
    """Tests for generate_parameterized_datasets function."""
    
    def test_multiple_thresholds(self):
        """Should generate datasets for multiple thresholds."""
        df = pd.DataFrame({
            'file_path': ['a.py', 'b.py', 'c.py'],
            'avg_loc': [5, 10, 15],
            'total_lines_changed': [10, 20, 30],
            'debt_score': [1, 2, 3],
            'contributor_count': [1, 1, 1]
        })
        
        datasets = generate_parameterized_datasets(df, thresholds=[5, 10, 20])
        
        assert 5 in datasets
        assert 10 in datasets
        assert 20 in datasets
        
        # Threshold 5: all 3 files
        assert len(datasets[5]) == 3
        # Threshold 10: 2 files (10, 15)
        assert len(datasets[10]) == 2
        # Threshold 20: 1 file (15)
        assert len(datasets[20]) == 1
    
    def test_default_thresholds(self):
        """Should use default thresholds [5, 10, 20] if not specified."""
        df = pd.DataFrame({
            'file_path': ['a.py'],
            'avg_loc': [10],
            'total_lines_changed': [10],
            'debt_score': [1],
            'contributor_count': [1]
        })
        
        datasets = generate_parameterized_datasets(df)
        
        assert len(datasets) == 3
        assert 5 in datasets
        assert 10 in datasets
        assert 20 in datasets

class TestValidateRawMetrics:
    """Tests for validate_raw_metrics function."""
    
    def test_valid_dataframe(self):
        """Should pass validation for valid dataframe."""
        df = pd.DataFrame({
            'file_path': ['a.py'],
            'total_lines_changed': [10],
            'debt_score': [1],
            'avg_loc': [15],
            'contributor_count': [1]
        })
        
        assert validate_raw_metrics(df) is True
    
    def test_missing_columns(self):
        """Should raise error for missing required columns."""
        df = pd.DataFrame({
            'file_path': ['a.py'],
            'total_lines_changed': [10]
        })
        
        with pytest.raises(ValueError, match="Missing required raw metric columns"):
            validate_raw_metrics(df)
    
    def test_null_values_warning(self):
        """Should handle null values (only warns, doesn't fail)."""
        df = pd.DataFrame({
            'file_path': ['a.py', 'b.py'],
            'total_lines_changed': [10, None],
            'debt_score': [1, 2],
            'avg_loc': [15, 20],
            'contributor_count': [1, 1]
        })
        
        # Should not raise, but log warning
        assert validate_raw_metrics(df) is True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])