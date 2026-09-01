import os
import json
import time
import tempfile
import pytest
from pathlib import Path

# Mock the config to use temp directories
import sys
from unittest.mock import patch, MagicMock

# Add code to path if not already
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from runtime_validator import run_dry_run_pipeline, generate_mock_data_for_dry_run
from config import get_results_path, get_path

@pytest.fixture
def temp_dirs():
    # Create temporary directories for this test
    with tempfile.TemporaryDirectory() as tmpdir:
        # We can't easily override the global config paths in config.py without reloading
        # So we will test the logic that doesn't strictly depend on global paths
        # or we patch the get_path functions
        yield tmpdir

def test_generate_mock_data_structure():
    """Test that mock data generation creates a valid CSV structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_mock.csv")
        generate_mock_data_for_dry_run(output_path, num_functions=3)
        
        assert os.path.exists(output_path)
        
        import pandas as pd
        df = pd.read_csv(output_path)
        
        assert len(df) == 3
        assert 'code' in df.columns
        assert 'static_smell_labels' in df.columns
        assert all(df['static_smell_labels'] == 'None')

def test_dry_run_pipeline_completion():
    """Test that the dry run pipeline completes successfully."""
    # Patch the config functions to return temp paths
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = os.path.join(tmpdir, "data")
        results_dir = os.path.join(tmpdir, "results")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "processed"), exist_ok=True)
        
        with patch('runtime_validator.get_path', return_value=data_dir), \
             patch('runtime_validator.get_results_path', return_value=results_dir):
             
            results = run_dry_run_pipeline(max_runtime_seconds=60.0)
            
            assert results['status'] == 'success'
            assert 'total_runtime_seconds' in results
            assert 'steps' in results
            assert 'generate_mock_data' in results['steps']
            assert 'mock_semantic_analysis' in results['steps']
            assert 'mock_statistical_analysis' in results['steps']
            
            # Verify report file was created
            report_path = os.path.join(results_dir, "runtime_dry_run_report.json")
            assert os.path.exists(report_path)
            
            with open(report_path, 'r') as f:
                saved_report = json.load(f)
                assert saved_report['status'] == 'success'

def test_runtime_within_limit():
    """Test that the dry run completes within the specified time limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = os.path.join(tmpdir, "data")
        results_dir = os.path.join(tmpdir, "results")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "processed"), exist_ok=True)
        
        limit = 60.0 # 60 seconds
        
        with patch('runtime_validator.get_path', return_value=data_dir), \
             patch('runtime_validator.get_results_path', return_value=results_dir):
             
            start = time.time()
            results = run_dry_run_pipeline(max_runtime_seconds=limit)
            elapsed = time.time() - start
            
            assert results['total_runtime_seconds'] < limit
            assert results['status'] == 'success'
            
            # Also check the saved report
            report_path = os.path.join(results_dir, "runtime_dry_run_report.json")
            with open(report_path, 'r') as f:
                report = json.load(f)
                assert report['total_runtime_seconds'] < limit