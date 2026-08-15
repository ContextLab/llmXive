import json
import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from run_matching_report import (
    calculate_baseline_stats,
    evaluate_matching_quality,
    load_json_file
)

def test_calculate_baseline_stats_empty():
    """Test baseline stats calculation with empty list."""
    stats = calculate_baseline_stats([])
    assert stats['loc_mean'] == 0.0
    assert stats['loc_std'] == 0.0
    assert stats['cc_mean'] == 0.0
    assert stats['cc_std'] == 0.0

def test_calculate_baseline_stats_single():
    """Test baseline stats calculation with single item."""
    metrics = [{'loc': 100, 'cyclomatic_complexity': 10}]
    stats = calculate_baseline_stats(metrics)
    assert stats['loc_mean'] == 100.0
    assert stats['loc_std'] == 0.0
    assert stats['cc_mean'] == 10.0
    assert stats['cc_std'] == 0.0

def test_calculate_baseline_stats_multiple():
    """Test baseline stats calculation with multiple items."""
    metrics = [
        {'loc': 100, 'cyclomatic_complexity': 10},
        {'loc': 200, 'cyclomatic_complexity': 20},
        {'loc': 300, 'cyclomatic_complexity': 30}
    ]
    stats = calculate_baseline_stats(metrics)
    # Mean of 100, 200, 300 is 200
    assert stats['loc_mean'] == 200.0
    # Mean of 10, 20, 30 is 20
    assert stats['cc_mean'] == 20.0
    # Variance of 100, 200, 300: ((100-200)^2 + (200-200)^2 + (300-200)^2) / 3 = (10000 + 0 + 10000)/3 = 6666.67
    # Std = sqrt(6666.67) ≈ 81.65
    assert abs(stats['loc_std'] - 81.6496580927726) < 0.01

def test_evaluate_matching_quality_within_tolerance():
    """Test evaluation when repo is within 15% tolerance."""
    repo = {'repo_id': 'test-repo', 'loc': 200, 'cyclomatic_complexity': 20}
    baseline = {'loc_mean': 200.0, 'loc_std': 50.0, 'cc_mean': 20.0, 'cc_std': 5.0}
    
    result = evaluate_matching_quality(repo, baseline)
    
    assert result['repo_id'] == 'test-repo'
    assert result['matching_quality']['loc_deviation_pct'] == 0.0
    assert result['matching_quality']['cc_deviation_pct'] == 0.0
    assert result['matching_quality']['within_loc_tolerance_15pct'] is True
    assert result['matching_quality']['within_cc_tolerance_15pct'] is True

def test_evaluate_matching_quality_outside_tolerance():
    """Test evaluation when repo is outside 15% tolerance."""
    repo = {'repo_id': 'test-repo', 'loc': 500, 'cyclomatic_complexity': 50}
    baseline = {'loc_mean': 200.0, 'loc_std': 50.0, 'cc_mean': 20.0, 'cc_std': 5.0}
    
    result = evaluate_matching_quality(repo, baseline)
    
    # (500 - 200) / 200 = 1.5 -> 150%
    assert result['matching_quality']['loc_deviation_pct'] == 150.0
    assert result['matching_quality']['within_loc_tolerance_15pct'] is False
    assert 'ANCOVA' in result['matching_quality']['notes']

def test_evaluate_matching_quality_retains_all():
    """Verify that the evaluation does not filter out repos."""
    # The function returns a dict for every input repo; it never raises or skips
    repo = {'repo_id': 'bad-repo', 'loc': 10000, 'cyclomatic_complexity': 1000}
    baseline = {'loc_mean': 200.0, 'loc_std': 50.0, 'cc_mean': 20.0, 'cc_std': 5.0}
    
    result = evaluate_matching_quality(repo, baseline)
    # Even though it's way off, it returns a valid result
    assert result is not None
    assert 'matching_quality' in result