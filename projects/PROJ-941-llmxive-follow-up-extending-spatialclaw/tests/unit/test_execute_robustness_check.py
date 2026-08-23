"""
Unit tests for T057b: Execute Robustness Check
"""
import os
import sys
import json
import tempfile
import csv
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

import pytest
from stats.execute_robustness_check import (
    load_latencies_by_type,
    run_shapiro_wilk_check,
    generate_methodology_log
)

@pytest.fixture
def sample_paired_data():
    """Sample paired dataset for testing."""
    return [
        {
            'task_id': 'task_001',
            'task_type': 'occlusion',
            '2d_mean_latency': 100.5,
            '3d_latency': 90.0,
            '2d_success_rate': 0.9,
            '3d_success': 1.0
        },
        {
            'task_id': 'task_002',
            'task_type': 'occlusion',
            '2d_mean_latency': 110.0,
            '3d_latency': 95.0,
            '2d_success_rate': 0.8,
            '3d_success': 1.0
        },
        {
            'task_id': 'task_003',
            'task_type': 'depth',
            '2d_mean_latency': 150.0,
            '3d_latency': 140.0,
            '2d_success_rate': 0.7,
            '3d_success': 1.0
        },
        {
            'task_id': 'task_004',
            'task_type': 'depth',
            '2d_mean_latency': 160.0,
            '3d_latency': 145.0,
            '2d_success_rate': 0.6,
            '3d_success': 1.0
        }
    ]

def test_load_latencies_by_type(sample_paired_data):
    """Test extraction of latency differences by task type."""
    latencies = load_latencies_by_type(sample_paired_data)
    
    assert 'occlusion' in latencies
    assert 'depth' in latencies
    
    # Check occlusion diffs: (100.5-90), (110-95) -> [10.5, 15.0]
    assert len(latencies['occlusion']) == 2
    assert abs(latencies['occlusion'][0] - 10.5) < 0.01
    assert abs(latencies['occlusion'][1] - 15.0) < 0.01
    
    # Check depth diffs: (150-140), (160-145) -> [10.0, 15.0]
    assert len(latencies['depth']) == 2
    assert abs(latencies['depth'][0] - 10.0) < 0.01
    assert abs(latencies['depth'][1] - 15.0) < 0.01

def test_run_shapiro_wilk_check_insufficient_data():
    """Test handling of insufficient data points."""
    latencies = {
        'small': [1.0, 2.0]  # Only 2 points
    }
    results = run_shapiro_wilk_check(latencies)
    
    assert results['small']['is_normal'] == False
    assert 'Insufficient data points' in results['small']['reason']
    assert 'Wilcoxon' in results['small']['recommendation']

def test_generate_methodology_log_normal_data():
    """Test report generation with normal data."""
    results = {
        'occlusion': {
            'statistic': 0.98,
            'p_value': 0.85,
            'is_normal': True,
            'reason': 'p-value (0.8500) >= 0.05',
            'recommendation': 'Use t-test (paired)'
        }
    }
    
    log_content = generate_methodology_log(results)
    
    assert "# Statistical Methodology Log" in log_content
    assert "✅ Satisfied" in log_content
    assert "Paired t-tests" in log_content

def test_generate_methodology_log_non_normal_data():
    """Test report generation with non-normal data."""
    results = {
        'occlusion': {
            'statistic': 0.85,
            'p_value': 0.01,
            'is_normal': False,
            'reason': 'p-value (0.0100) < 0.05',
            'recommendation': 'Use non-parametric test (Wilcoxon)'
        }
    }
    
    log_content = generate_methodology_log(results)
    
    assert "❌ Violated" in log_content
    assert "Wilcoxon signed-rank" in log_content