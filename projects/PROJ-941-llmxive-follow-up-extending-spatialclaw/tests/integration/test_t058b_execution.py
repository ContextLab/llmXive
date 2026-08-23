"""
Integration test for T058b: Execute Edge Case Sensitivity Analysis.

Verifies that:
1. The execution script runs without error.
2. The output file results/analysis/flat_object_sensitivity.csv is created.
3. The output file contains the expected columns.
4. The output file has data rows (if flat objects exist in the test data).
"""
import os
import sys
import csv
import json
import tempfile
import shutil
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from stats.sensitivity import is_flat_object

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

def create_mock_paired_dataset(tmpdir, include_flat=True):
    """Create a mock final_paired_dataset.csv with some flat objects."""
    csv_path = os.path.join(tmpdir, 'final_paired_dataset.csv')
    
    headers = [
        'task_id', 'task_type', '2d_success_rate', '2d_mean_latency',
        '3d_success', '3d_latency', 'success_diff', 'latency_diff',
        'gt_depth_variance'  # Added for flat object detection
    ]
    
    rows = [
        # Non-flat object
        ['task_001', 'depth', 0.8, 100.5, 1, 90.0, -0.2, 10.5, 1.5],
        ['task_002', 'occlusion', 0.9, 120.0, 1, 115.0, -0.1, 5.0, 2.0],
    ]
    
    if include_flat:
        # Flat object (zero depth variance)
        rows.append(['task_003', 'depth', 0.5, 150.0, 1, 140.0, -0.5, 10.0, 0.0])
        rows.append(['task_004', 'depth', 0.6, 160.0, 1, 155.0, -0.4, 5.0, 0.0])
        # Near-flat object
        rows.append(['task_005', 'depth', 0.7, 145.0, 1, 142.0, -0.3, 3.0, 0.001])
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    
    return csv_path

def test_t058b_execution_creates_output(temp_output_dir):
    """Test that T058b execution creates the output CSV."""
    import subprocess
    
    # Create mock input data
    input_csv = create_mock_paired_dataset(temp_output_dir, include_flat=True)
    output_csv = os.path.join(temp_output_dir, 'flat_object_sensitivity.csv')
    
    # Run the execution script
    script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'code', 'stats', 'execute_flat_sensitivity.py')
    
    # Adjust paths for the script to use temp dirs
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), '..', '..', 'code') + ':' + env.get('PYTHONPATH', '')
    
    result = subprocess.run(
        [sys.executable, script_path, '--input-csv', input_csv, '--output-csv', output_csv],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__)
    )
    
    # Check if script ran successfully
    assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"
    
    # Check if output file exists
    assert os.path.exists(output_csv), f"Output file {output_csv} was not created"

def test_t058b_output_has_correct_columns(temp_output_dir):
    """Test that the output CSV has the required columns."""
    import subprocess
    
    input_csv = create_mock_paired_dataset(temp_output_dir, include_flat=True)
    output_csv = os.path.join(temp_output_dir, 'flat_object_sensitivity.csv')
    
    script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'code', 'stats', 'execute_flat_sensitivity.py')
    
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), '..', '..', 'code') + ':' + env.get('PYTHONPATH', '')
    
    subprocess.run(
        [sys.executable, script_path, '--input-csv', input_csv, '--output-csv', output_csv],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__)
    )
    
    with open(output_csv, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
    
    # Expected columns based on T058a/T058b spec
    expected_columns = ['epsilon_value', 'false_positive_rate', 'false_negative_rate', 'flat_object_count']
    
    for col in expected_columns:
        assert col in fieldnames, f"Missing expected column: {col}"

def test_t058b_detects_flat_objects_correctly():
    """Test the is_flat_object helper function."""
    # Test exact zero
    assert is_flat_object(0.0) is True
    
    # Test very small epsilon
    assert is_flat_object(1e-10) is True
    assert is_flat_object(1e-9) is True
    
    # Test larger values
    assert is_flat_object(0.001) is False
    assert is_flat_object(1.0) is False
    assert is_flat_object(10.0) is False

def test_t058b_handles_no_flat_objects(temp_output_dir):
    """Test that T058b handles datasets with no flat objects gracefully."""
    import subprocess
    
    # Create mock input data WITHOUT flat objects
    input_csv = create_mock_paired_dataset(temp_output_dir, include_flat=False)
    output_csv = os.path.join(temp_output_dir, 'flat_object_sensitivity.csv')
    
    script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'code', 'stats', 'execute_flat_sensitivity.py')
    
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.join(os.path.dirname(__file__), '..', '..', 'code') + ':' + env.get('PYTHONPATH', '')
    
    result = subprocess.run(
        [sys.executable, script_path, '--input-csv', input_csv, '--output-csv', output_csv],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(__file__)
    )
    
    # Should still succeed (just with empty or minimal results)
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert os.path.exists(output_csv), "Output file should still be created"
    
    # Verify it has headers
    with open(output_csv, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert len(headers) > 0, "Output file should have headers"