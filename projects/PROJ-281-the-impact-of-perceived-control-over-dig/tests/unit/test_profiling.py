"""
Unit tests for performance profiling module.
"""
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.profiling import (
    get_memory_usage_gb,
    run_profiling_pipeline,
    MAX_RUNTIME_SECONDS,
    MAX_RAM_GB
)

def test_get_memory_usage_gb():
    """Test that memory usage returns a positive float."""
    mem = get_memory_usage_gb()
    assert isinstance(mem, float)
    assert mem > 0

@patch('code.profiling.run_pipeline')
def test_run_profiling_pipeline_success(mock_run_pipeline, tmp_path):
    """Test successful pipeline execution and report generation."""
    mock_run_pipeline.return_value = None
    
    # Mock time to ensure fast execution for test
    with patch('code.profiling.time.time') as mock_time:
        mock_time.side_effect = [0, 10]  # 10 seconds runtime
        
        with patch('code.profiling.get_memory_usage_gb') as mock_mem:
            mock_mem.return_value = 2.0
            
            with patch('code.profiling.get_peak_memory_gb') as mock_peak:
                mock_peak.return_value = 2.5
                
                report = run_profiling_pipeline()
                
                assert report['pipeline_execution']['status'] == 'success'
                assert report['pipeline_execution']['runtime_seconds'] == 10
                assert report['validation']['runtime_pass'] is True
                assert report['validation']['memory_pass'] is True
                assert report['validation']['overall_pass'] is True

@patch('code.profiling.run_pipeline')
def test_run_profiling_pipeline_timeout(mock_run_pipeline, tmp_path):
    """Test pipeline failure due to runtime exceeding limit."""
    mock_run_pipeline.return_value = None
    
    with patch('code.profiling.time.time') as mock_time:
        # Simulate 7 hours runtime
        mock_time.side_effect = [0, 6 * 60 * 60 + 3600]
        
        with patch('code.profiling.get_memory_usage_gb') as mock_mem:
            mock_mem.return_value = 2.0
            
            with patch('code.profiling.get_peak_memory_gb') as mock_peak:
                mock_peak.return_value = 2.0
                
                report = run_profiling_pipeline()
                
                assert report['validation']['runtime_pass'] is False
                assert report['validation']['overall_pass'] is False

@patch('code.profiling.run_pipeline')
def test_run_profiling_pipeline_memory_exceeded(mock_run_pipeline, tmp_path):
    """Test pipeline failure due to memory exceeding limit."""
    mock_run_pipeline.return_value = None
    
    with patch('code.profiling.time.time') as mock_time:
        mock_time.side_effect = [0, 100]
        
        with patch('code.profiling.get_memory_usage_gb') as mock_mem:
            mock_mem.return_value = 2.0
            
            with patch('code.profiling.get_peak_memory_gb') as mock_peak:
                mock_peak.return_value = 8.0  # Exceeds 7GB
                
                report = run_profiling_pipeline()
                
                assert report['validation']['memory_pass'] is False
                assert report['validation']['overall_pass'] is False
