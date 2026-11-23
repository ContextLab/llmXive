"""
Unit tests for the performance benchmarking logic.
These tests verify that the benchmark script correctly measures time/memory
and handles edge cases (like missing data) without crashing.
"""
import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from performance_benchmark import (
    load_subset_epochs,
    benchmark_ica,
    benchmark_permutation,
    run_benchmark,
    MAX_WALL_CLOCK_HOURS,
    MAX_MEMORY_GB
)

@pytest.fixture
def mock_epochs():
    """Create a mock MNE Epochs object for testing."""
    mock = MagicMock()
    mock.events = np.random.randint(0, 100, (50, 3))
    mock.event_ids = {"standard": 1, "deviant": 2}
    mock.info = {"sfreq": 250.0, "ch_names": ["Fz", "Cz", "Pz"]}
    mock.pick_types = MagicMock(return_value=mock)
    mock.get_data = MagicMock(return_value=np.random.rand(50, 3, 20))
    mock.__len__ = lambda self: 50
    return mock

def test_load_subset_epochs_missing_file(tmp_path):
    """Test that load_subset_epochs returns None when file is missing."""
    with patch('performance_benchmark.get_project_root') as mock_root:
        mock_root.return_value = tmp_path
        result = load_subset_epochs()
        assert result is None

def test_benchmark_ica_memory_limit(mock_epochs):
    """Test that benchmark_ica correctly reports memory usage."""
    # Mock the measure function to return a specific memory usage
    with patch('performance_benchmark.measure_function_duration_and_memory') as mock_measure:
        mock_measure.return_value = {
            'duration_seconds': 10.0,
            'peak_memory_gb': 2.0
        }
        
        with patch('performance_benchmark.detect_ica_components'):
            result = benchmark_ica(mock_epochs)
            
            assert result['step'] == 'ica'
            assert result['status'] == 'passed'
            assert result['peak_memory_gb'] == 2.0

def test_benchmark_permutation_skipped_missing_metrics(tmp_path):
    """Test that permutation benchmark is skipped if metrics.csv is missing."""
    with patch('performance_benchmark.get_project_root') as mock_root:
        mock_root.return_value = tmp_path
        
        # Ensure metrics.csv does not exist
        metrics_path = tmp_path / "results" / "metrics.csv"
        
        result = benchmark_permutation(None, metrics_path)
        
        assert result['status'] == 'skipped_data_missing'

def test_benchmark_permutation_memory_limit(mock_epochs, tmp_path):
    """Test that permutation benchmark correctly reports memory usage."""
    # Create a dummy metrics file
    metrics_path = tmp_path / "results" / "metrics.csv"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text("participant_id,standard_amplitude\nsub-01,1.0\n")
    
    with patch('performance_benchmark.measure_function_duration_and_memory') as mock_measure:
        mock_measure.return_value = {
            'duration_seconds': 20.0,
            'peak_memory_gb': 3.5
        }
        
        with patch('performance_benchmark.run_cluster_based_permutation_test') as mock_stats:
            mock_stats.return_value = {"result": "dummy"}
            
            result = benchmark_permutation(mock_epochs, metrics_path)
            
            assert result['step'] == 'permutation'
            assert result['status'] == 'passed'
            assert result['peak_memory_gb'] == 3.5

def test_run_benchmark_integration(mock_epochs, tmp_path):
    """Integration test for the full benchmark run (mocked)."""
    with patch('performance_benchmark.get_project_root') as mock_root:
        mock_root.return_value = tmp_path
        
        # Mock load_subset_epochs to return our mock
        with patch('performance_benchmark.load_subset_epochs', return_value=mock_epochs):
            # Mock the individual benchmarks
            with patch('performance_benchmark.benchmark_ica') as mock_ica:
                mock_ica.return_value = {
                    'step': 'ica',
                    'duration_seconds': 100.0,
                    'peak_memory_gb': 1.0,
                    'status': 'passed'
                }
                
                with patch('performance_benchmark.benchmark_permutation') as mock_perm:
                    mock_perm.return_value = {
                        'step': 'permutation',
                        'duration_seconds': 200.0,
                        'peak_memory_gb': 2.0,
                        'status': 'passed'
                    }
                    
                    # Mock ensure_directory
                    with patch('performance_benchmark.ensure_directory'):
                        result = run_benchmark()
                        
                        assert result['summary']['overall_status'] == 'passed'
                        assert result['summary']['total_duration_hours'] < MAX_WALL_CLOCK_HOURS
                        
                        # Check that report was written
                        report_path = tmp_path / "results" / "performance_benchmark.json"
                        assert report_path.exists()
                        
                        with open(report_path) as f:
                            data = json.load(f)
                            assert 'summary' in data
