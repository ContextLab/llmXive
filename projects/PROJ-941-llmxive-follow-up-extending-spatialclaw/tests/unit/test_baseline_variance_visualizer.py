"""
Unit tests for T063: Baseline Variance Visualization
"""
import os
import json
import tempfile
import shutil
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Import the module
import sys
sys.path.insert(0, 'code')
from stats.baseline_variance_visualizer import (
    load_baseline_runs_metadata,
    load_2d_agent_runs,
    extract_metrics_from_runs,
    plot_variance_comparison
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory structure for testing."""
    tmp = tempfile.mkdtemp()
    # Create necessary subdirectories
    os.makedirs(os.path.join(tmp, "results", "runs"), exist_ok=True)
    os.makedirs(os.path.join(tmp, "results", "logs"), exist_ok=True)
    os.makedirs(os.path.join(tmp, "results", "analysis"), exist_ok=True)
    yield tmp
    shutil.rmtree(tmp)

@pytest.fixture
def mock_baseline_runs(temp_dir):
    """Create mock baseline run files."""
    runs_dir = os.path.join(temp_dir, "results", "runs")
    # Create 3 mock baseline runs
    for i in range(3):
        data = [
            {"task_id": f"task_{j}", "latency_ms": 100.0 + (i * 5), "success_flag": 1.0}
            for j in range(10)
        ]
        with open(os.path.join(runs_dir, f"baseline_run_{i}.json"), 'w') as f:
            json.dump(data, f)
    return runs_dir

@pytest.fixture
def mock_2d_runs(temp_dir):
    """Create mock 2D agent run files."""
    runs_dir = os.path.join(temp_dir, "results", "runs")
    # Create 3 mock 2D runs
    for i in range(3):
        data = [
            {"task_id": f"task_{j}", "latency_ms": 120.0 + (i * 10) + np.random.normal(0, 5), "success_flag": 0.9}
            for j in range(10)
        ]
        with open(os.path.join(runs_dir, f"run_{i}.json"), 'w') as f:
            json.dump(data, f)
    return runs_dir

def test_load_baseline_runs_metadata(mock_baseline_runs, temp_dir):
    """Test loading baseline run metadata."""
    # Change to temp dir to simulate project root
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        runs = load_baseline_runs_metadata()
        assert len(runs) == 3
        for run in runs:
            assert "run_id" in run
            assert "data" in run
            assert len(run["data"]) == 10
    finally:
        os.chdir(old_cwd)

def test_load_2d_agent_runs(mock_2d_runs, temp_dir):
    """Test loading 2D agent run data."""
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        runs = load_2d_agent_runs()
        assert len(runs) == 3
        for run in runs:
            assert "run_id" in run
            assert "data" in run
    finally:
        os.chdir(old_cwd)

def test_extract_metrics_from_runs():
    """Test metric extraction logic."""
    test_data = [
        {
            "run_id": 0,
            "data": [
                {"latency_ms": 100.0, "success_flag": 1.0},
                {"latency_ms": 110.0, "success_flag": 0.0}
            ]
        },
        {
            "run_id": 1,
            "data": [
                {"latency_ms": 105.0, "success_flag": 1.0},
                {"latency_ms": 115.0, "success_flag": 1.0}
            ]
        }
    ]
    
    latencies, success = extract_metrics_from_runs(test_data)
    
    # Run 0: mean latency (100+110)/2 = 105, mean success 0.5
    assert abs(latencies[0] - 105.0) < 0.01
    assert abs(success[0] - 0.5) < 0.01
    
    # Run 1: mean latency (105+115)/2 = 110, mean success 1.0
    assert abs(latencies[1] - 110.0) < 0.01
    assert abs(success[1] - 1.0) < 0.01

def test_plot_variance_comparison(temp_dir):
    """Test that the plot is generated successfully."""
    output_path = os.path.join(temp_dir, "results", "analysis", "test_plot.png")
    
    base_lat = [100.0, 105.0, 110.0]
    base_succ = [1.0, 1.0, 0.9]
    two_d_lat = [120.0, 130.0, 140.0]
    two_d_succ = [0.9, 0.8, 0.85]
    
    plot_variance_comparison(base_lat, base_succ, two_d_lat, two_d_succ, output_path)
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0