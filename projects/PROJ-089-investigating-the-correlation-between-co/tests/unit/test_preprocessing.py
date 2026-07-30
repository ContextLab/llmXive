"""
Unit tests for preprocessing module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from preprocessing import (
    is_source_file,
    should_exclude_dir,
    filter_non_source_files,
    apply_loc_threshold,
    generate_parameterized_datasets,
    validate_raw_metrics,
)

class TestIsSourceFile:
    def test_known_extensions(self):
        """Test recognized source file extensions."""
        assert is_source_file("file.py") is True
        assert is_source_file("file.java") is True
        assert is_source_file("file.js") is True
        assert is_source_file("file.ts") is True
        assert is_source_file("file.go") is True
        assert is_source_file("file.rs") is True
        assert is_source_file("file.c") is True
        assert is_source_file("file.cpp") is True
        assert is_source_file("file.rb") is True
        assert is_source_file("file.php") is True
        assert is_source_file("file.swift") is True
        assert is_source_file("file.kt") is True
        assert is_source_file("file.scala") is True
        assert is_source_file("file.r") is True
        assert is_source_file("file.jl") is True
        assert is_source_file("file.sh") is True
        assert is_source_file("file.html") is True
        assert is_source_file("file.css") is True
        assert is_source_file("file.sql") is True
        assert is_source_file("file.md") is True
    
    def test_unknown_extensions(self):
        """Test unrecognized file extensions."""
        assert is_source_file("file.xyz") is False
        assert is_source_file("file.exe") is False
        assert is_source_file("file.bin") is False
        assert is_source_file("file") is False  # No extension
    
    def test_case_insensitive(self):
        """Test that extension matching is case-insensitive."""
        assert is_source_file("file.PY") is True
        assert is_source_file("file.Py") is True
        assert is_source_file("file.JAVA") is True

class TestShouldExcludeDir:
    def test_excluded_dirs(self):
        """Test known excluded directory names."""
        assert should_exclude_dir("node_modules") is True
        assert should_exclude_dir("__pycache__") is True
        assert should_exclude_dir(".git") is True
        assert should_exclude_dir("venv") is True
        assert should_exclude_dir("dist") is True
        assert should_exclude_dir("build") is True
        assert should_exclude_dir("target") is True
        assert should_exclude_dir("vendor") is True
    
    def test_excluded_patterns(self):
        """Test directory names matching exclusion patterns."""
        assert should_exclude_dir("tests") is True
        assert should_exclude_dir("test") is True
        assert should_exclude_dir("spec") is True
        assert should_exclude_dir("specs") is True
        assert should_exclude_dir("mocks") is True
        assert should_exclude_dir("mock") is True
        assert should_exclude_dir("fixtures") is True
        assert should_exclude_dir("examples") is True
        assert should_exclude_dir("generated") is True
    
    def test_case_insensitive(self):
        """Test that directory exclusion is case-insensitive."""
        assert should_exclude_dir("NODE_MODULES") is True
        assert should_exclude_dir("Node_Modules") is True
        assert should_exclude_dir("TESTS") is True
    
    def test_allowed_dirs(self):
        """Test directories that should NOT be excluded."""
        assert should_exclude_dir("src") is False
        assert should_exclude_dir("lib") is False
        assert should_exclude_dir("app") is False
        assert should_exclude_dir("core") is False
        assert should_exclude_dir("utils") is False
        assert should_exclude_dir("main") is False

class TestFilterNonSourceFiles:
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'file_path': [
                'src/main.py',
                'src/test.py',
                'lib/utils.js',
                'node_modules/pkg/index.js',
                'data/file.csv',
                'docs/readme.md',
                'app/App.java',
                'tests/test_main.py',
                'build/output.class',
                'src/components/App.tsx',
            ],
            'total_lines_changed': [10, 5, 20, 100, 50, 30, 15, 8, 200, 12],
            'debt_score': [2, 1, 5, 50, 10, 8, 3, 2, 100, 4],
            'avg_loc': [50, 30, 100, 500, 200, 150, 80, 40, 600, 60],
            'contributor_count': [3, 1, 2, 10, 5, 3, 2, 1, 15, 2],
        })
    
    def test_filters_non_source_files(self, sample_df):
        """Test that non-source files are filtered out."""
        result = filter_non_source_files(sample_df)
        
        # Check that only source files remain
        for path in result['file_path']:
            assert is_source_file(path) is True
            assert not should_exclude_dir(Path(path).parent.name)
    
    def test_filters_excluded_directories(self, sample_df):
        """Test that files in excluded directories are filtered out."""
        result = filter_non_source_files(sample_df)
        
        excluded_paths = ['node_modules/pkg/index.js', 'tests/test_main.py']
        for path in excluded_paths:
            assert path not in result['file_path'].values
    
    def test_preserves_source_files(self, sample_df):
        """Test that source files in valid directories are preserved."""
        result = filter_non_source_files(sample_df)
        
        expected_paths = [
            'src/main.py',
            'src/test.py',  # test.py in src/ is a source file
            'lib/utils.js',
            'docs/readme.md',
            'app/App.java',
            'src/components/App.tsx',
        ]
        
        for path in expected_paths:
            assert path in result['file_path'].values
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame(columns=['file_path', 'total_lines_changed'])
        result = filter_non_source_files(empty_df)
        assert result.empty is True

class TestApplyLocThreshold:
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'file_path': ['file1.py', 'file2.py', 'file3.py', 'file4.py'],
            'avg_loc': [5, 15, 25, 100],
            'total_lines_changed': [10, 20, 30, 40],
            'debt_score': [1, 2, 3, 4],
            'contributor_count': [1, 2, 3, 4],
        })
    
    def test_filters_below_threshold(self, sample_df):
        """Test filtering files below the LOC threshold."""
        result = apply_loc_threshold(sample_df, min_loc=10)
        
        assert len(result) == 3  # 15, 25, 100
        assert all(result['avg_loc'] >= 10)
    
    def test_filters_below_higher_threshold(self, sample_df):
        """Test filtering with a higher threshold."""
        result = apply_loc_threshold(sample_df, min_loc=50)
        
        assert len(result) == 2  # 100 only
        assert all(result['avg_loc'] >= 50)
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame(columns=['file_path', 'avg_loc'])
        result = apply_loc_threshold(empty_df, min_loc=10)
        assert result.empty is True
    
    def test_missing_column(self, sample_df):
        """Test error when required column is missing."""
        df = sample_df.drop(columns=['avg_loc'])
        with pytest.raises(ValueError, match="avg_loc"):
            apply_loc_threshold(df, min_loc=10)

class TestValidateRawMetrics:
    @pytest.fixture
    def valid_df(self):
        """Create a valid DataFrame for testing."""
        return pd.DataFrame({
            'total_lines_changed': [10, 20, 30],
            'debt_score': [1, 2, 3],
            'avg_loc': [50, 60, 70],
            'contributor_count': [2, 3, 4],
        })
    
    def test_valid_dataframe(self, valid_df):
        """Test validation passes for valid data."""
        assert validate_raw_metrics(valid_df) is True
    
    def test_missing_column(self, valid_df):
        """Test error when required column is missing."""
        df = valid_df.drop(columns=['total_lines_changed'])
        with pytest.raises(ValueError, match="total_lines_changed"):
            validate_raw_metrics(df)
    
    def test_null_values(self, valid_df):
        """Test error when null values are present."""
        df = valid_df.copy()
        df.loc[0, 'avg_loc'] = None
        with pytest.raises(ValueError, match="null values"):
            validate_raw_metrics(df)
    
    def test_negative_values(self, valid_df):
        """Test error when negative values are present."""
        df = valid_df.copy()
        df.loc[0, 'total_lines_changed'] = -10
        with pytest.raises(ValueError, match="negative values"):
            validate_raw_metrics(df)

class TestGenerateParameterizedDatasets:
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'file_path': ['file1.py', 'file2.py', 'file3.py', 'file4.py'],
            'avg_loc': [5, 15, 25, 100],
            'total_lines_changed': [10, 20, 30, 40],
            'debt_score': [1, 2, 3, 4],
            'contributor_count': [1, 2, 3, 4],
        })
    
    def test_generates_all_thresholds(self, sample_df):
        """Test that datasets are generated for all thresholds."""
        datasets = generate_parameterized_datasets(sample_df, thresholds=[5, 10, 20])
        
        assert len(datasets) == 3
        assert 5 in datasets
        assert 10 in datasets
        assert 20 in datasets
    
    def test_correct_sizes(self, sample_df):
        """Test that dataset sizes match expected counts."""
        datasets = generate_parameterized_datasets(sample_df, thresholds=[5, 10, 20])
        
        # Threshold 5: all 4 files (5, 15, 25, 100 >= 5)
        assert len(datasets[5]) == 4
        
        # Threshold 10: 3 files (15, 25, 100 >= 10)
        assert len(datasets[10]) == 3
        
        # Threshold 20: 2 files (25, 100 >= 20)
        assert len(datasets[20]) == 2
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame(columns=['file_path', 'avg_loc'])
        datasets = generate_parameterized_datasets(empty_df, thresholds=[5, 10, 20])
        
        assert len(datasets) == 3
        for df in datasets.values():
            assert df.empty is True
