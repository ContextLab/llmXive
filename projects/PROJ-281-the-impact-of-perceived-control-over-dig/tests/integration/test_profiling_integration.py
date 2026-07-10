"""
Integration test for the full profiling pipeline.

This test verifies that the profiling script can be executed end-to-end
and produces a valid performance report JSON file.
"""
import json
import tempfile
from pathlib import Path

import pytest

from code.profiling import save_report, run_profiling_pipeline
from code.config import CONFIG

def test_save_report_creates_file(tmp_path):
    """Test that save_report creates a valid JSON file."""
    report_data = {
        "test": "data",
        "value": 123
    }
    output_path = tmp_path / "test_report.json"
    
    save_report(report_data, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        loaded_data = json.load(f)
        
    assert loaded_data == report_data

def test_profiling_report_structure():
    """
    Verify the structure of the performance report.
    
    Note: This test mocks the actual pipeline execution to avoid
    long runtime during testing.
    """
    import time
    from unittest.mock import patch, MagicMock
    
    with patch('code.profiling.run_pipeline') as mock_pipeline:
        mock_pipeline.return_value = None
        
        with patch('code.profiling.time.time') as mock_time:
            mock_time.side_effect = [0, 1]
            
            with patch('code.profiling.get_memory_usage_gb') as mock_mem:
                mock_mem.return_value = 1.0
                
                with patch('code.profiling.get_peak_memory_gb') as mock_peak:
                    mock_peak.return_value = 1.5
                    
                    report = run_profiling_pipeline()
                    
                    # Check required keys
                    assert 'pipeline_execution' in report
                    assert 'constraints' in report
                    assert 'validation' in report
                    
                    # Check pipeline execution fields
                    exec_data = report['pipeline_execution']
                    assert 'status' in exec_data
                    assert 'runtime_seconds' in exec_data
                    assert 'peak_memory_gb' in exec_data
                    
                    # Check validation fields
                    val_data = report['validation']
                    assert 'runtime_pass' in val_data
                    assert 'memory_pass' in val_data
                    assert 'overall_pass' in val_data
                    
                    # Verify types
                    assert isinstance(exec_data['runtime_seconds'], float)
                    assert isinstance(exec_data['peak_memory_gb'], float)
                    assert isinstance(val_data['runtime_pass'], bool)
                    assert isinstance(val_data['memory_pass'], bool)
                    assert isinstance(val_data['overall_pass'], bool)
