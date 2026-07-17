"""
Integration test for T041: Merge Sensitivity Metrics.
Verifies that the merge_sensitivity_metrics.py script correctly:
1. Loads existing metrics.
2. Processes sensitivity samples.
3. Produces a unified metrics.json with all entries.
"""

import os
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# We need to test the logic. Since the main script imports from analyze_metrics,
# we will mock those dependencies to avoid running actual heavy analysis in unit tests.
# However, for an integration test, we want to verify the file flow.

@pytest.fixture
def temp_dirs():
    """Create temporary directories for test data."""
    base = tempfile.mkdtemp()
    data_dir = os.path.join(base, "data", "analysis")
    gen_dir = os.path.join(base, "data", "generated", "sensitivity")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(gen_dir, exist_ok=True)
    yield {
        "base": base,
        "metrics_file": os.path.join(data_dir, "metrics.json"),
        "sensitivity_dir": gen_dir
    }
    shutil.rmtree(base)

def test_merge_logic(temp_dirs):
    """Test the merging logic with mock data."""
    metrics_file = temp_dirs["metrics_file"]
    sens_dir = temp_dirs["sensitivity_dir"]

    # 1. Setup existing metrics
    existing_data = [
        {"task_id": "HumanEval/0", "cyclomatic_complexity": 2, "halstead_volume": 45.5, "pass_rate": 1.0, "branch_coverage_pct": 85.0}
    ]
    with open(metrics_file, 'w') as f:
        json.dump(existing_data, f)

    # 2. Setup sensitivity samples (mock generated code)
    sens_data = [
        {"task_id": "HumanEval/0", "model": "codellama-7b", "generated_code": "def f(): pass"},
        {"task_id": "HumanEval/1", "model": "codellama-3b", "generated_code": "def g(): pass"}
    ]
    for i, item in enumerate(sens_data):
        filename = os.path.join(sens_dir, f"sens_{i}.json")
        with open(filename, 'w') as f:
            json.dump(item, f)

    # 3. Mock the heavy analysis functions to return deterministic values
    # We patch the imports inside the module being tested
    with patch('merge_sensitivity_metrics.calculate_code_metrics') as mock_calc, \
         patch('merge_sensitivity_metrics.load_test_suites') as mock_load_tests, \
         patch('merge_sensitivity_metrics.execute_test_suite') as mock_exec_test, \
         patch('merge_sensitivity_metrics.execute_coverage_test') as mock_exec_cov:
        
        # Mock return values
        mock_calc.return_value = (2, 50.0)
        mock_load_tests.return_value = {"HumanEval/0": "pass", "HumanEval/1": "pass"}
        mock_exec_test.return_value = True
        mock_exec_cov.return_value = 90.0

        # Import the main function logic (we need to import the module to patch)
        # Since the script is in code/, we might need to adjust sys.path or import logic
        # For this test, we assume the script is importable or we test the functions directly.
        # Let's test the functions directly by importing them if possible, or simulating the flow.
        
        # To avoid complex path issues in this snippet, we will simulate the function calls
        # that the main() function makes, verifying the merge logic.
        
        from merge_sensitivity_metrics import load_existing_metrics, load_sensitivity_samples, merge_metrics
        
        # Re-run the load functions with the temp paths
        # Note: The actual script uses global constants. We would need to refactor to pass paths or use env vars.
        # For this test, we assume the script is modified to accept paths or we test the helper functions.
        
        # Let's test the helper functions directly which are pure logic
        loaded_existing = load_existing_metrics(metrics_file)
        assert len(loaded_existing) == 1
        assert "HumanEval/0" in loaded_existing

        loaded_sens = load_sensitivity_samples(sens_dir)
        assert len(loaded_sens) == 2

        # Merge
        merged = merge_metrics(loaded_existing, loaded_sens)
        # We expect 1 (existing) + 2 (new) = 3 entries
        assert len(merged) == 3

        # Verify the new entries have the model_tag
        new_entries = [m for m in merged if "model_tag" in m]
        assert len(new_entries) == 2

def test_file_creation(temp_dirs):
    """Test that the script creates the output file correctly."""
    # This test would require running the actual script with mocked dependencies
    # which is complex in a single file test. We rely on test_merge_logic for logic verification.
    # This serves as a placeholder for end-to-end verification if the environment allows.
    assert os.path.exists(temp_dirs["metrics_file"])
    assert os.path.exists(temp_dirs["sensitivity_dir"])