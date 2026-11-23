"""
Tests for class imbalance handling module.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import json

from src.imbalance_handler import (
    detect_class_imbalance,
    filter_imbalanced_projects,
    save_imbalance_report,
    ClassImbalanceError
)


@pytest.fixture
def balanced_data():
    """Create a balanced dataset with mixed buggy/non-buggy projects."""
    data = {
        'project_id': ['proj_a'] * 10 + ['proj_b'] * 10 + ['proj_c'] * 10,
        'cc': [10] * 30,
        'halstead': [100.0] * 30,
        'loc': [100] * 30,
        'is_buggy': [0] * 5 + [1] * 5 + [0] * 10 + [1] * 5 + [0] * 10
    }
    return pd.DataFrame(data)


@pytest.fixture
def zero_buggy_data():
    """Create a dataset with one project having zero buggy files."""
    data = {
        'project_id': ['proj_x'] * 5 + ['proj_y'] * 5,
        'cc': [10] * 10,
        'halstead': [100.0] * 10,
        'loc': [100] * 10,
        'is_buggy': [0] * 5 + [1] * 5
    }
    return pd.DataFrame(data)


@pytest.fixture
def all_buggy_data():
    """Create a dataset with one project having all buggy files."""
    data = {
        'project_id': ['proj_x'] * 5 + ['proj_y'] * 5,
        'cc': [10] * 10,
        'halstead': [100.0] * 10,
        'loc': [100] * 10,
        'is_buggy': [1] * 5 + [1] * 5
    }
    return pd.DataFrame(data)


class TestDetectClassImbalance:
    """Tests for detect_class_imbalance function."""
    
    def test_detect_zero_buggy(self, zero_buggy_data):
        """Test detection of projects with zero buggy files."""
        result = detect_class_imbalance(zero_buggy_data)
        
        assert 'zero_buggy' in result
        assert 'all_buggy' in result
        assert 'proj_x' in result['zero_buggy']
        assert 'proj_y' not in result['zero_buggy']
        assert len(result['all_buggy']) == 0
    
    def test_detect_all_buggy(self, all_buggy_data):
        """Test detection of projects with all buggy files."""
        result = detect_class_imbalance(all_buggy_data)
        
        assert 'zero_buggy' in result
        assert 'all_buggy' in result
        assert 'proj_x' in result['all_buggy']
        assert 'proj_y' in result['all_buggy']
        assert len(result['zero_buggy']) == 0
    
    def test_balanced_data(self, balanced_data):
        """Test that balanced data has no flagged projects."""
        result = detect_class_imbalance(balanced_data)
        
        assert len(result['zero_buggy']) == 0
        assert len(result['all_buggy']) == 0
    
    def test_missing_project_column(self, zero_buggy_data):
        """Test error when project_id column is missing."""
        df = zero_buggy_data.rename(columns={'project_id': 'wrong_name'})
        
        with pytest.raises(ValueError, match="Column 'project_id' not found"):
            detect_class_imbalance(df)
    
    def test_missing_target_column(self, zero_buggy_data):
        """Test error when target column is missing."""
        df = zero_buggy_data.rename(columns={'is_buggy': 'wrong_name'})
        
        with pytest.raises(ValueError, match="Column 'is_buggy' not found"):
            detect_class_imbalance(df, target_col='is_buggy')


class TestFilterImbalancedProjects:
    """Tests for filter_imbalanced_projects function."""
    
    def test_filter_zero_buggy(self, zero_buggy_data):
        """Test that projects with zero buggy files are removed."""
        filtered_df, stats = filter_imbalanced_projects(zero_buggy_data)
        
        assert 'proj_x' not in filtered_df['project_id'].values
        assert 'proj_y' in filtered_df['project_id'].values
        assert stats['removed_count'] == 5
        assert 'proj_x' in stats['zero_buggy']
    
    def test_filter_all_buggy(self, all_buggy_data):
        """Test that projects with all buggy files are removed."""
        filtered_df, stats = filter_imbalanced_projects(all_buggy_data)
        
        assert len(filtered_df) == 0
        assert stats['removed_count'] == 10
        assert 'proj_x' in stats['all_buggy']
        assert 'proj_y' in stats['all_buggy']
    
    def test_filter_low_ratio(self):
        """Test filtering based on low buggy ratio."""
        data = {
            'project_id': ['proj_a'] * 100 + ['proj_b'] * 10,
            'is_buggy': [1] + [0] * 99 + [1] * 10  # proj_a has 1% buggy
        }
        df = pd.DataFrame(data)
        
        # With default min_buggy_ratio=0.01, proj_a should be kept (exactly 1%)
        filtered_df, stats = filter_imbalanced_projects(df, min_buggy_ratio=0.01)
        assert 'proj_a' in filtered_df['project_id'].values
        
        # With higher threshold, proj_a should be removed
        filtered_df2, stats2 = filter_imbalanced_projects(df, min_buggy_ratio=0.02)
        assert 'proj_a' not in filtered_df2['project_id'].values
        assert len(stats2['low_buggy']) == 1
    
    def test_filter_by_count(self):
        """Test filtering based on minimum buggy count."""
        data = {
            'project_id': ['proj_a'] * 100 + ['proj_b'] * 10,
            'is_buggy': [1, 1] + [0] * 98 + [1] * 10  # proj_a has 2 buggy files
        }
        df = pd.DataFrame(data)
        
        # With min_buggy_count=1, both should be kept
        filtered_df, stats = filter_imbalanced_projects(df, min_buggy_count=1)
        assert len(filtered_df) == 110
        
        # With min_buggy_count=3, proj_a should be removed
        filtered_df2, stats2 = filter_imbalanced_projects(df, min_buggy_count=3)
        assert 'proj_a' not in filtered_df2['project_id'].values
        assert len(stats2['low_buggy']) == 1
    
    def test_no_imbalance(self, balanced_data):
        """Test that balanced data is returned unchanged."""
        filtered_df, stats = filter_imbalanced_projects(balanced_data)
        
        assert len(filtered_df) == len(balanced_data)
        assert stats['removed_count'] == 0
        assert len(stats['removed_projects']) == 0
    
    def test_returns_stats(self, zero_buggy_data):
        """Test that stats dictionary has all required keys."""
        _, stats = filter_imbalanced_projects(zero_buggy_data)
        
        required_keys = ['removed_projects', 'removed_count', 'zero_buggy', 
                       'all_buggy', 'low_buggy']
        for key in required_keys:
            assert key in stats


class TestSaveImbalanceReport:
    """Tests for save_imbalance_report function."""
    
    def test_save_report(self):
        """Test saving imbalance report to JSON."""
        stats = {
            'removed_projects': ['proj_a', 'proj_b'],
            'removed_count': 15,
            'zero_buggy': ['proj_a'],
            'all_buggy': ['proj_b'],
            'low_buggy': []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'report.json'
            save_imbalance_report(stats, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert 'summary' in report
            assert 'details' in report
            assert report['summary']['total_removed_projects'] == 2
            assert report['summary']['total_removed_rows'] == 15
            assert report['details']['zero_buggy_projects'] == ['proj_a']
            assert report['details']['all_buggy_projects'] == ['proj_b']
    
    def test_creates_directories(self):
        """Test that report saving creates parent directories."""
        stats = {
            'removed_projects': [],
            'removed_count': 0,
            'zero_buggy': [],
            'all_buggy': [],
            'low_buggy': []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'subdir1' / 'subdir2' / 'report.json'
            save_imbalance_report(stats, output_path)
            
            assert output_path.exists()