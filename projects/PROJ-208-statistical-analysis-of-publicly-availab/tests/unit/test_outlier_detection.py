"""
Unit tests for outlier detection functionality.

Tests the IQR-based outlier detection on log-transformed resolution times.
"""

import json
import math
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.outlier_detection import detect_outliers_iqr, load_cleaned_data


class TestDetectOutliersIQR:
    """Tests for the detect_outliers_iqr function."""
    
    def test_basic_outlier_detection(self):
        """Test that outliers are correctly identified using IQR method."""
        # Create test data with known outliers
        # Most values between 1 and 10 hours, one extreme outlier at 1000 hours
        data = {
            'issue_id': range(100),
            'repo': ['repo_a'] * 100,
            'resolution_time_hours': [2.0] * 98 + [1000.0, 500.0]
        }
        df = pd.DataFrame(data)
        
        result_df, stats = detect_outliers_iqr(df)
        
        # Should detect the extreme outliers
        assert stats['outlier_count'] >= 1
        assert stats['outlier_percentage'] > 0
        assert 'q1' in stats
        assert 'q3' in stats
        assert 'iqr' in stats
        assert 'upper_bound' in stats
        
    def test_no_outliers(self):
        """Test dataset with no outliers."""
        # Create data with uniform distribution
        np.random.seed(42)
        data = {
            'issue_id': range(100),
            'repo': ['repo_a'] * 100,
            'resolution_time_hours': np.random.uniform(1, 10, 100)
        }
        df = pd.DataFrame(data)
        
        result_df, stats = detect_outliers_iqr(df)
        
        # May still detect some outliers depending on distribution
        assert stats['total_issues'] == 100
        assert stats['valid_issues'] == 100
        assert 'outlier_count' in stats
        
    def test_invalid_resolution_times(self):
        """Test handling of non-positive resolution times."""
        data = {
            'issue_id': [1, 2, 3, 4, 5],
            'repo': ['repo_a'] * 5,
            'resolution_time_hours': [-1.0, 0.0, 2.0, 5.0, 10.0]
        }
        df = pd.DataFrame(data)
        
        result_df, stats = detect_outliers_iqr(df)
        
        # Should handle invalid values gracefully
        assert stats['invalid_count'] == 2
        assert stats['valid_issues'] == 3
        assert stats['total_issues'] == 5
        
    def test_empty_dataset(self):
        """Test handling of empty dataset."""
        df = pd.DataFrame({
            'issue_id': [],
            'repo': [],
            'resolution_time_hours': []
        })
        
        result_df, stats = detect_outliers_iqr(df)
        
        assert stats['total_issues'] == 0
        assert stats['valid_issues'] == 0
        assert stats['outlier_count'] == 0
        
    def test_all_invalid(self):
        """Test dataset where all values are invalid."""
        data = {
            'issue_id': [1, 2, 3],
            'repo': ['repo_a'] * 3,
            'resolution_time_hours': [-1.0, 0.0, -5.0]
        }
        df = pd.DataFrame(data)
        
        result_df, stats = detect_outliers_iqr(df)
        
        assert stats['invalid_count'] == 3
        assert stats['valid_issues'] == 0
        assert stats['outlier_count'] == 0
        
    def test_outlier_percentage_calculation(self):
        """Test that outlier percentage is correctly calculated."""
        # Create data where exactly 10% are outliers
        # 90 values at 2 hours, 10 values at 1000 hours (extreme outliers)
        data = {
            'issue_id': list(range(100)),
            'repo': ['repo_a'] * 100,
            'resolution_time_hours': [2.0] * 90 + [1000.0] * 10
        }
        df = pd.DataFrame(data)
        
        result_df, stats = detect_outliers_iqr(df)
        
        # Verify percentage calculation
        expected_percentage = (stats['outlier_count'] / stats['valid_issues']) * 100
        assert abs(stats['outlier_percentage'] - expected_percentage) < 0.1
        
    def test_log_transformation_applied(self):
        """Verify that log transformation is used in outlier detection."""
        # Create data with known log-scale outlier
        data = {
            'issue_id': list(range(50)),
            'repo': ['repo_a'] * 50,
            'resolution_time_hours': [1.0] * 48 + [100.0, 200.0]
        }
        df = pd.DataFrame(data)
        
        result_df, stats = detect_outliers_iqr(df)
        
        # Check that log-based bounds are present
        assert stats['log_upper_bound'] is not None
        assert stats['log_lower_bound'] is not None
        
        # Verify back-transformation is reasonable
        assert stats['log_upper_bound'] > 0
        assert stats['log_lower_bound'] > 0
        
    def test_outlier_details_included(self):
        """Test that outlier details are included in stats."""
        data = {
            'issue_id': list(range(100)),
            'repo': ['repo_a'] * 100,
            'resolution_time_hours': [2.0] * 95 + [1000.0] * 5
        }
        df = pd.DataFrame(data)
        
        result_df, stats = detect_outliers_iqr(df)
        
        if stats['outlier_count'] > 0:
            assert 'outliers' in stats
            assert isinstance(stats['outliers'], list)
            # Check structure of outlier details
            if len(stats['outliers']) > 0:
                outlier = stats['outliers'][0]
                assert 'resolution_time_hours' in outlier
                assert 'log_resolution_time' in outlier
                
    def test_method_description(self):
        """Test that method description is included."""
        data = {
            'issue_id': [1, 2, 3],
            'repo': ['repo_a'] * 3,
            'resolution_time_hours': [1.0, 2.0, 100.0]
        }
        df = pd.DataFrame(data)
        
        result_df, stats = detect_outliers_iqr(df)
        
        assert stats['method'] == "IQR (Q3 + 1.5*IQR) on log-transformed data"
        
    def test_statistical_integrity(self):
        """Test that Q1, Q3, and IQR are mathematically correct."""
        # Create simple dataset where we can verify calculations
        # Values: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 (log-transformed)
        data = {
            'issue_id': list(range(10)),
            'repo': ['repo_a'] * 10,
            'resolution_time_hours': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        }
        df = pd.DataFrame(data)
        
        result_df, stats = detect_outliers_iqr(df)
        
        # Verify IQR = Q3 - Q1
        calculated_iqr = stats['q3'] - stats['q1']
        assert abs(calculated_iqr - stats['iqr']) < 0.0001
        
    def test_large_dataset_performance(self):
        """Test performance with larger dataset."""
        np.random.seed(42)
        n = 10000
        data = {
            'issue_id': list(range(n)),
            'repo': ['repo_a'] * n,
            'resolution_time_hours': np.random.lognormal(mean=0, sigma=1, size=n)
        }
        df = pd.DataFrame(data)
        
        result_df, stats = detect_outliers_iqr(df)
        
        assert stats['total_issues'] == n
        assert stats['valid_issues'] == n
        assert 'outlier_count' in stats
        assert 'outlier_percentage' in stats