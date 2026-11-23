"""
Tests for the performance validation module.
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from validate_performance import (
    validate_pipeline_performance,
    load_pipeline_timing_results,
    DEFAULT_EXECUTION_THRESHOLD_SECONDS
)

@pytest.fixture
def sample_timing_results():
    """Sample timing results for testing."""
    return {
        'total_execution_time_seconds': 120.5,
        'stage_times': {
            'ingestion': 15.2,
            'descriptors': 45.8,
            'standardize': 10.1,
            'analysis': 35.4,
            'visualization': 14.0
        },
        'pipeline_version': '1.0.0',
        'timestamp': '2024-01-01 12:00:00'
    }

@pytest.fixture
def slow_timing_results():
    """Sample timing results that exceed threshold."""
    return {
        'total_execution_time_seconds': 450.0,
        'stage_times': {
            'ingestion': 100.0,
            'descriptors': 150.0,
            'standardize': 50.0,
            'analysis': 100.0,
            'visualization': 50.0
        },
        'pipeline_version': '1.0.0',
        'timestamp': '2024-01-01 12:00:00'
    }

def test_validate_pipeline_performance_pass(sample_timing_results):
    """Test that validation passes when execution time is under threshold."""
    threshold = 300.0
    result = validate_pipeline_performance(sample_timing_results, threshold)
    
    assert result['passed'] is True
    assert result['threshold_seconds'] == threshold
    assert result['actual_execution_time_seconds'] == 120.5
    assert result['margin_seconds'] == 179.5
    assert result['details']['status'] == 'PASS'

def test_validate_pipeline_performance_fail(slow_timing_results):
    """Test that validation fails when execution time exceeds threshold."""
    threshold = 300.0
    result = validate_pipeline_performance(slow_timing_results, threshold)
    
    assert result['passed'] is False
    assert result['threshold_seconds'] == threshold
    assert result['actual_execution_time_seconds'] == 450.0
    assert result['margin_seconds'] == -150.0
    assert result['details']['status'] == 'FAIL'

def test_validate_pipeline_performance_default_threshold():
    """Test validation with default threshold."""
    timing_results = {
        'total_execution_time_seconds': DEFAULT_EXECUTION_THRESHOLD_SECONDS - 1,
        'stage_times': {}
    }
    
    result = validate_pipeline_performance(timing_results)
    assert result['passed'] is True
    assert result['threshold_seconds'] == DEFAULT_EXECUTION_THRESHOLD_SECONDS

def test_validate_pipeline_performance_edge_case():
    """Test validation when execution time exactly equals threshold."""
    threshold = 300.0
    timing_results = {
        'total_execution_time_seconds': threshold,
        'stage_times': {}
    }
    
    result = validate_pipeline_performance(timing_results, threshold)
    assert result['passed'] is True  # Equal to threshold should pass
    assert result['margin_seconds'] == 0.0

def test_validate_pipeline_performance_stage_breakdown(sample_timing_results):
    """Test that stage breakdown is preserved in results."""
    result = validate_pipeline_performance(sample_timing_results, 300.0)
    
    assert 'stage_breakdown' in result
    assert result['stage_breakdown'] == sample_timing_results['stage_times']
    assert 'ingestion' in result['stage_breakdown']
    assert 'analysis' in result['stage_breakdown']

def test_load_pipeline_timing_results_file_not_found():
    """Test that FileNotFoundError is raised for missing timing file."""
    with pytest.raises(FileNotFoundError):
        load_pipeline_timing_results('nonexistent_file.json')

def test_load_pipeline_timing_results(tmp_path):
    """Test loading timing results from a valid file."""
    timing_data = {
        'total_execution_time_seconds': 100.0,
        'stage_times': {'test': 10.0}
    }
    
    timing_file = tmp_path / "timing.json"
    with open(timing_file, 'w') as f:
        json.dump(timing_data, f)
    
    result = load_pipeline_timing_results(str(timing_file))
    assert result == timing_data
    assert result['total_execution_time_seconds'] == 100.0
