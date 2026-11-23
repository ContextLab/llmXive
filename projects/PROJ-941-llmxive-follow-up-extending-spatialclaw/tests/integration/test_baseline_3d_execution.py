"""
tests/integration/test_baseline_3d_execution.py

Integration test for T023b: Verify that the 3D baseline agent can be executed
on the Synthetic SpatialClaw Proxy dataset and produces the expected output file.

This test ensures:
1. The input dataset (data/raw/synthetic_spatialclaw_v1.json) exists.
2. The baseline script runs without error.
3. The output file (results/logs/baseline_run.json) is created.
4. The output file contains valid JSON with the required schema.
"""

import os
import json
import subprocess
import sys
import tempfile
import pytest

# Define paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'synthetic_spatialclaw_v1.json')
BASELINE_SCRIPT = os.path.join(PROJECT_ROOT, 'code', 'agents', 'baseline_3d.py')
OUTPUT_RESULTS_PATH = os.path.join(PROJECT_ROOT, 'results', 'logs', 'baseline_run.json')

@pytest.fixture(scope="module")
def ensure_output_dir():
    """Ensure the output directory exists before running tests."""
    os.makedirs(os.path.dirname(OUTPUT_RESULTS_PATH), exist_ok=True)

@pytest.mark.integration
def test_baseline_execution_creates_output(ensure_output_dir):
    """Test that running the baseline script creates the output JSON file."""
    
    # Check if input data exists (prerequisite T006b)
    if not os.path.exists(INPUT_DATA_PATH):
        pytest.skip(f"Input dataset not found at {INPUT_DATA_PATH}. Prerequisite T006b not met.")

    # Construct command
    cmd = [
        sys.executable,
        BASELINE_SCRIPT,
        '--input', INPUT_DATA_PATH,
        '--output', OUTPUT_RESULTS_PATH,
        '--log-level', 'INFO'
    ]

    # Run the script
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Assert command succeeded
    assert result.returncode == 0, f"Baseline script failed: {result.stderr}"

    # Assert output file exists
    assert os.path.exists(OUTPUT_RESULTS_PATH), f"Output file not created: {OUTPUT_RESULTS_PATH}"

@pytest.mark.integration
def test_baseline_output_schema():
    """Test that the output JSON file matches the expected schema."""
    
    if not os.path.exists(OUTPUT_RESULTS_PATH):
        pytest.skip(f"Output file not found at {OUTPUT_RESULTS_PATH}. Run test_baseline_execution first.")

    with open(OUTPUT_RESULTS_PATH, 'r') as f:
        data = json.load(f)

    assert isinstance(data, list), "Output data must be a list of results."
    assert len(data) > 0, "Output data must contain at least one result."

    required_fields = {'task_id', 'task_type', 'success', 'latency_ms'}
    
    for i, item in enumerate(data):
        assert isinstance(item, dict), f"Item {i} must be a dictionary."
        missing = required_fields - set(item.keys())
        assert not missing, f"Item {i} missing required fields: {missing}"
        
        # Type checks
        assert isinstance(item['task_id'], str), "task_id must be string"
        assert isinstance(item['task_type'], str), "task_type must be string"
        assert isinstance(item['success'], bool), "success must be boolean"
        assert isinstance(item['latency_ms'], (int, float)), "latency_ms must be numeric"

@pytest.mark.integration
def test_baseline_success_rate():
    """
    Verify that the 3D baseline agent achieves a high success rate.
    Since this is the 'ideal' 3D agent, it should succeed on almost all tasks
    where the ground truth is well-defined.
    """
    
    if not os.path.exists(OUTPUT_RESULTS_PATH):
        pytest.skip(f"Output file not found at {OUTPUT_RESULTS_PATH}.")

    with open(OUTPUT_RESULTS_PATH, 'r') as f:
        data = json.load(f)

    if not data:
        pytest.skip("No data to analyze.")

    success_count = sum(1 for item in data if item['success'])
    total_count = len(data)
    success_rate = success_count / total_count

    # The 3D baseline should be very reliable (e.g., > 90% success)
    # If it fails, it indicates a logic error in the baseline implementation.
    assert success_rate > 0.9, f"3D Baseline success rate too low: {success_rate:.2%}"
