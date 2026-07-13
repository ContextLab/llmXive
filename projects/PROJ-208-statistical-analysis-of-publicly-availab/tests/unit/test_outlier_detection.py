import pytest
import numpy as np
from pathlib import Path
import sys
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.outlier_detection import detect_outliers, calculate_outlier_metrics

@pytest.fixture
def sample_issues():
    """Create a sample list of issues for testing."""
    return [
        {'number': 1, 'repository': 'repo1', 'resolution_time_hours': 10.0},
        {'number': 2, 'repository': 'repo1', 'resolution_time_hours': 24.0},
        {'number': 3, 'repository': 'repo2', 'resolution_time_hours': 500.0},  # > 30 days
        {'number': 4, 'repository': 'repo2', 'resolution_time_hours': 720.0},  # > 30 days (30 days)
        {'number': 5, 'repository': 'repo3', 'resolution_time_hours': 100.0},
        {'number': 6, 'repository': 'repo3', 'resolution_time_hours': 800.0},  # > 30 days
        {'number': 7, 'repository': 'repo4', 'resolution_time_hours': 5.0},
        {'number': 8, 'repository': 'repo4', 'resolution_time_hours': np.nan},  # Missing value
        {'number': 9, 'repository': 'repo5', 'resolution_time_hours': 750.0},   # > 30 days
    ]

@pytest.fixture
def empty_issues():
    """Create an empty list of issues."""
    return []

def test_detect_outliers_basic(sample_issues):
    """Test basic outlier detection with 30-day threshold."""
    outliers, non_outliers = detect_outliers(sample_issues, threshold_days=30.0)
    
    # 30 days = 720 hours
    # Outliers: issues with resolution_time_hours > 720
    # Issue 3: 500h (not outlier)
    # Issue 4: 720h (not outlier, exactly 30 days)
    # Issue 6: 800h (outlier)
    # Issue 9: 750h (outlier)
    # Issue 8: NaN (skipped)
    
    # Expected outliers: issues with 750h and 800h
    assert len(outliers) == 2
    
    # Check that outliers are indeed > 720 hours
    for issue in outliers:
        assert issue['resolution_time_hours'] > 720.0
    
    # Check that non-outliers are <= 720 hours or NaN
    for issue in non_outliers:
        if issue.get('resolution_time_hours') is not None and not np.isnan(issue['resolution_time_hours']):
            assert issue['resolution_time_hours'] <= 720.0

def test_detect_outliers_custom_threshold(sample_issues):
    """Test outlier detection with a custom threshold."""
    # Use 10-day threshold (240 hours)
    outliers, non_outliers = detect_outliers(sample_issues, threshold_days=10.0)
    
    # Issues > 240 hours: 500, 720, 800, 750
    assert len(outliers) == 4
    
    for issue in outliers:
        assert issue['resolution_time_hours'] > 240.0

def test_detect_outliers_empty_data(empty_issues):
    """Test outlier detection with empty data."""
    outliers, non_outliers = detect_outliers(empty_issues, threshold_days=30.0)
    
    assert len(outliers) == 0
    assert len(non_outliers) == 0

def test_detect_outliers_all_outliers():
    """Test when all issues are outliers."""
    issues = [
        {'number': 1, 'repository': 'repo1', 'resolution_time_hours': 1000.0},
        {'number': 2, 'repository': 'repo2', 'resolution_time_hours': 2000.0},
    ]
    
    outliers, non_outliers = detect_outliers(issues, threshold_days=30.0)
    
    assert len(outliers) == 2
    assert len(non_outliers) == 0

def test_detect_outliers_none_outliers():
    """Test when no issues are outliers."""
    issues = [
        {'number': 1, 'repository': 'repo1', 'resolution_time_hours': 10.0},
        {'number': 2, 'repository': 'repo2', 'resolution_time_hours': 100.0},
        {'number': 3, 'repository': 'repo3', 'resolution_time_hours': 500.0},
    ]
    
    outliers, non_outliers = detect_outliers(issues, threshold_days=30.0)
    
    assert len(outliers) == 0
    assert len(non_outliers) == 3

def test_detect_outliers_handles_missing_values(sample_issues):
    """Test that missing values are handled correctly."""
    outliers, non_outliers = detect_outliers(sample_issues, threshold_days=30.0)
    
    # Issue 8 has NaN and should be skipped
    # Check that no NaN values are in either list
    for issue in outliers:
        assert issue.get('resolution_time_hours') is not None
        assert not np.isnan(issue['resolution_time_hours'])
    
    for issue in non_outliers:
        if issue.get('resolution_time_hours') is not None:
            assert not np.isnan(issue['resolution_time_hours'])

def test_calculate_outlier_metrics_basic(sample_issues):
    """Test basic metric calculation."""
    outliers, _ = detect_outliers(sample_issues, threshold_days=30.0)
    metrics = calculate_outlier_metrics(outliers, len(sample_issues))
    
    assert metrics['outlier_count'] == 2
    assert metrics['outlier_percentage'] == (2 / len(sample_issues)) * 100.0
    assert metrics['max_resolution_time_hours'] > 0
    assert metrics['mean_resolution_time_hours'] > 0
    assert metrics['median_resolution_time_hours'] > 0

def test_calculate_outlier_metrics_empty_outliers(sample_issues):
    """Test metric calculation when there are no outliers."""
    outliers, _ = detect_outliers(sample_issues, threshold_days=1000.0)  # High threshold
    metrics = calculate_outlier_metrics(outliers, len(sample_issues))
    
    assert metrics['outlier_count'] == 0
    assert metrics['outlier_percentage'] == 0.0
    assert metrics['max_resolution_time_hours'] == 0.0
    assert metrics['mean_resolution_time_hours'] == 0.0
    assert metrics['median_resolution_time_hours'] == 0.0

def test_calculate_outlier_metrics_zero_total():
    """Test metric calculation with zero total issues."""
    metrics = calculate_outlier_metrics([], 0)
    
    assert metrics['outlier_count'] == 0
    assert metrics['outlier_percentage'] == 0.0
    assert metrics['max_resolution_time_hours'] == 0.0

def test_calculate_outlier_metrics_with_missing_values():
    """Test metric calculation with outliers containing missing values."""
    issues_with_nan = [
        {'number': 1, 'repository': 'repo1', 'resolution_time_hours': 1000.0},
        {'number': 2, 'repository': 'repo2', 'resolution_time_hours': np.nan},
        {'number': 3, 'repository': 'repo3', 'resolution_time_hours': 2000.0},
    ]
    
    metrics = calculate_outlier_metrics(issues_with_nan, 3)
    
    # Should only consider non-NaN values
    assert metrics['outlier_count'] == 3  # All are in the input list
    assert metrics['mean_resolution_time_hours'] == 1500.0  # Mean of 1000 and 2000
    assert metrics['max_resolution_time_hours'] == 2000.0

def test_outlier_percentage_calculation():
    """Test that outlier percentage is calculated correctly."""
    outliers = [{'resolution_time_hours': 1000.0}]
    total_issues = 100
    
    metrics = calculate_outlier_metrics(outliers, total_issues)
    
    assert metrics['outlier_percentage'] == 1.0  # 1/100 * 100
