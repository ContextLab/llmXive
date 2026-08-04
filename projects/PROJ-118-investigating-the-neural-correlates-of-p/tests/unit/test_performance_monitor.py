"""
Unit tests for performance_monitor.py
Tests the logic of performance measurement and reporting without running the full pipeline.
"""
import pytest
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from performance_monitor import (
    get_memory_usage_gb,
    measure_function_duration_and_memory,
    generate_report,
    TIME_LIMIT_SECONDS,
    MEMORY_LIMIT_GB
)

def test_get_memory_usage_gb():
    """Test that memory usage is returned as a positive float."""
    mem = get_memory_usage_gb()
    assert isinstance(mem, float)
    assert mem > 0

def test_measure_function_duration_and_memory():
    """Test that the measurement function returns correct structure."""
    def dummy_func():
        time.sleep(0.1)
        return "success"
    
    result = measure_function_duration_and_memory(dummy_func)
    
    assert 'duration_seconds' in result
    assert 'peak_memory_gb' in result
    assert 'start_memory_gb' in result
    assert 'end_memory_gb' in result
    assert 'success' in result
    assert result['success'] is True
    assert result['result'] == "success"
    assert result['duration_seconds'] >= 0.1

def test_measure_function_duration_and_memory_failure():
    """Test that the measurement function handles exceptions correctly."""
    def failing_func():
        raise ValueError("Test error")
    
    result = measure_function_duration_and_memory(failing_func)
    
    assert result['success'] is False
    assert 'error' not in result  # The error is logged, not returned in this simple version
    assert result['duration_seconds'] >= 0

def test_generate_report(tmp_path):
    """Test that generate_report creates a valid JSON file."""
    # Mock project_root to use tmp_path
    with patch('performance_monitor.project_root', tmp_path):
        results = {
            'test_stage': {
                'duration_seconds': 100.0,
                'peak_memory_gb': 2.5,
                'success': True
            }
        }
        
        report_path = tmp_path / 'results' / 'performance_report.json'
        generate_report(results)
        
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
        
        assert 'timestamp' in report
        assert 'constraints' in report
        assert 'stages' in report
        assert 'summary' in report
        assert report['summary']['passed_time_constraint'] is True
        assert report['summary']['passed_memory_constraint'] is True

def test_generate_report_failure_scenario(tmp_path):
    """Test report generation when constraints are violated."""
    with patch('performance_monitor.project_root', tmp_path):
        results = {
            'test_stage': {
                'duration_seconds': TIME_LIMIT_SECONDS + 100,  # Exceeds limit
                'peak_memory_gb': MEMORY_LIMIT_GB + 1,  # Exceeds limit
                'success': True
            }
        }
        
        generate_report(results)
        
        report_path = tmp_path / 'results' / 'performance_report.json'
        with open(report_path) as f:
            report = json.load(f)
        
        assert report['summary']['passed_time_constraint'] is False
        assert report['summary']['passed_memory_constraint'] is False
