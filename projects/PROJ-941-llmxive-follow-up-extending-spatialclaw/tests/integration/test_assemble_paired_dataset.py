"""
Integration tests for the assemble_paired_dataset module.
Verifies the end-to-end flow of merging 2D and 3D results.
"""
import os
import json
import csv
import tempfile
import shutil
import pytest
from pathlib import Path

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis.assemble_paired_dataset import (
    load_baseline_results,
    load_2d_run_results,
    aggregate_2d_results,
    build_paired_dataset,
    write_csv,
    main
)

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create directory structure
    runs_dir = os.path.join(temp_dir, 'results', 'runs')
    logs_dir = os.path.join(temp_dir, 'results', 'logs')
    analysis_dir = os.path.join(temp_dir, 'results', 'analysis')
    
    os.makedirs(runs_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(analysis_dir, exist_ok=True)
    
    # Create mock baseline results
    baseline_data = [
        {
            "task_id": "task_001",
            "task_type": "occlusion",
            "success": True,
            "latency_ms": 100.5
        },
        {
            "task_id": "task_002",
            "task_type": "depth",
            "success": False,
            "latency_ms": 150.2
        },
        {
            "task_id": "task_003",
            "task_type": "relative",
            "success": True,
            "latency_ms": 120.0
        }
    ]
    
    baseline_path = os.path.join(logs_dir, "baseline_run.json")
    with open(baseline_path, 'w') as f:
        json.dump(baseline_data, f)
    
    # Create mock 2D run results (5 runs per task)
    for run_id in range(5):
        run_data = []
        # Task 001: 5 successes
        run_data.append({
            "task_id": "task_001",
            "task_type": "occlusion",
            "success": True,
            "latency_ms": 200.0 + run_id
        })
        # Task 002: 3 successes, 2 failures
        run_data.append({
            "task_id": "task_002",
            "task_type": "depth",
            "success": run_id < 3,
            "latency_ms": 250.0 + run_id
        })
        # Task 003: 5 successes
        run_data.append({
            "task_id": "task_003",
            "task_type": "relative",
            "success": True,
            "latency_ms": 180.0 + run_id
        })
        
        run_path = os.path.join(runs_dir, f"run_{run_id}.json")
        with open(run_path, 'w') as f:
            json.dump(run_data, f)
    
    yield {
        'temp_dir': temp_dir,
        'runs_dir': runs_dir,
        'baseline_path': baseline_path,
        'output_path': os.path.join(analysis_dir, "test_paired_dataset.csv")
    }
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_load_baseline_results(temp_workspace):
    """Test loading baseline results."""
    baseline_map = load_baseline_results(temp_workspace['baseline_path'])
    
    assert len(baseline_map) == 3
    assert 'task_001' in baseline_map
    assert baseline_map['task_001']['success'] is True
    assert baseline_map['task_002']['success'] is False

def test_load_2d_run_results(temp_workspace):
    """Test loading 2D run results."""
    run_results = load_2d_run_results(temp_workspace['runs_dir'])
    
    # 3 tasks * 5 runs = 15 results
    assert len(run_results) == 15

def test_aggregate_2d_results(temp_workspace):
    """Test aggregation of 2D results."""
    run_results = load_2d_run_results(temp_workspace['runs_dir'])
    aggregated = aggregate_2d_results(run_results, n_runs_expected=5)
    
    assert len(aggregated) == 3
    
    # Task 001: 5/5 success = 1.0
    assert aggregated['task_001']['2d_success_rate'] == 1.0
    assert aggregated['task_001']['n_runs'] == 5
    
    # Task 002: 3/5 success = 0.6
    assert aggregated['task_002']['2d_success_rate'] == 0.6
    assert aggregated['task_002']['n_runs'] == 5

def test_build_paired_dataset(temp_workspace):
    """Test building the paired dataset."""
    baseline_map = load_baseline_results(temp_workspace['baseline_path'])
    run_results = load_2d_run_results(temp_workspace['runs_dir'])
    aggregated_2d = aggregate_2d_results(run_results, n_runs_expected=5)
    
    paired = build_paired_dataset(baseline_map, aggregated_2d)
    
    assert len(paired) == 3
    
    # Check sorting
    task_ids = [row['task_id'] for row in paired]
    assert task_ids == sorted(task_ids)
    
    # Check task_001 specifics
    task_001 = next(row for row in paired if row['task_id'] == 'task_001')
    assert task_001['task_type'] == 'occlusion'
    assert task_001['2d_success_rate'] == 1.0
    assert task_001['3d_success'] == 1
    assert task_001['success_diff'] == 0.0  # 1.0 - 1.0

def test_write_csv_and_validation(temp_workspace):
    """Test writing CSV and null value validation."""
    baseline_map = load_baseline_results(temp_workspace['baseline_path'])
    run_results = load_2d_run_results(temp_workspace['runs_dir'])
    aggregated_2d = aggregate_2d_results(run_results, n_runs_expected=5)
    paired = build_paired_dataset(baseline_map, aggregated_2d)
    
    write_csv(paired, temp_workspace['output_path'])
    
    assert os.path.exists(temp_workspace['output_path'])
    
    # Read back and verify
    with open(temp_workspace['output_path'], 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    
    # Verify column names
    expected_cols = ['task_id', 'task_type', '2d_success_rate', '2d_mean_latency', 
                    '3d_success', '3d_latency', 'success_diff', 'latency_diff']
    assert list(rows[0].keys()) == expected_cols

def test_main_function(temp_workspace):
    """Test the main function end-to-end."""
    # Change to temp dir to simulate real execution
    old_cwd = os.getcwd()
    try:
        os.chdir(temp_workspace['temp_dir'])
        
        # Create a minimal config
        config_path = os.path.join(temp_workspace['temp_dir'], 'data')
        os.makedirs(config_path, exist_ok=True)
        with open(os.path.join(config_path, 'power_config.yaml'), 'w') as f:
            f.write("n_runs: 5\n")
        
        # Run main
        import sys
        sys.argv = [
            'test',
            '--config', os.path.join(config_path, 'power_config.yaml'),
            '--baseline', temp_workspace['baseline_path'],
            '--runs-dir', temp_workspace['runs_dir'],
            '--output', temp_workspace['output_path']
        ]
        
        main()
        
        assert os.path.exists(temp_workspace['output_path'])
        
    finally:
        os.chdir(old_cwd)
        sys.argv = ['test']

def test_missing_baseline_raises_error():
    """Test that missing baseline file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_baseline_results('/nonexistent/path.json')

def test_missing_runs_dir_raises_error():
    """Test that missing runs directory raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_2d_run_results('/nonexistent/dir')

def test_null_value_detection():
    """Test that null values in critical columns are detected."""
    data_with_null = [
        {
            'task_id': None,  # Critical column null
            'task_type': 'occlusion',
            '2d_success_rate': 0.5,
            '2d_mean_latency': 100.0,
            '3d_success': 1,
            '3d_latency': 120.0,
            'success_diff': -0.5,
            'latency_diff': -20.0
        }
    ]
    
    with pytest.raises(ValueError, match="missing or null value in critical column"):
        write_csv(data_with_null, '/tmp/test_null.csv')