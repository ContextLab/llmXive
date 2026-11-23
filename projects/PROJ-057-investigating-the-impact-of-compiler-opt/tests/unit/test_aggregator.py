import pytest
import pandas as pd
from pathlib import Path
import shutil
import json

# Ensure we can import from code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.aggregator import aggregate_results, generate_final_pareto

@pytest.fixture
def setup_test_data(tmp_path):
    """Create dummy raw logs and stability metrics for testing."""
    raw_logs_dir = tmp_path / "data" / "intermediates" / "raw_logs"
    results_dir = tmp_path / "data" / "results"
    raw_logs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy raw log
    log_data = [
        {
            "config_id": "test_001",
            "kernel_type": "matmul",
            "median": 0.005,
            "p95": 0.006,
            "iterations": 1000,
            "output_tensor": [1.0, 2.0, 3.0]
        },
        {
            "config_id": "test_002",
            "kernel_type": "softmax",
            "median": 0.003,
            "p95": 0.004,
            "iterations": 1000,
            "output_tensor": [0.1, 0.9]
        }
    ]
    with open(raw_logs_dir / "test_log.jsonl", "w") as f:
        for item in log_data:
            f.write(json.dumps(item) + "\n")

    # Create a dummy stability metrics CSV
    stability_data = [
        {"config_id": "test_001", "kernel_type": "matmul", "l2_error": "1e-6", "max_diff": "1e-7", "status": "stable"},
        {"config_id": "test_002", "kernel_type": "softmax", "l2_error": "1e-4", "max_diff": "1e-5", "status": "stable"}
    ]
    df_stab = pd.DataFrame(stability_data)
    df_stab.to_csv(results_dir / "stability_metrics.csv", index=False)

    return tmp_path

def test_aggregate_results(setup_test_data):
    """Test that aggregate_results merges latency and stability data correctly."""
    # Patch paths to use temp directory
    # Note: In a real scenario, we might refactor aggregate_results to accept paths
    # For this unit test, we assume the function reads from default relative paths
    # which we cannot easily override without refactoring. 
    # However, to test the logic, we verify the function exists and signature.
    # A more robust integration test would be needed for full path override.
    
    # Since we can't easily override the hardcoded paths in aggregate_results without refactoring,
    # we will assert that the function is callable and returns a DataFrame if data exists.
    # For the purpose of this task, we verify the logic by checking the function signature and imports.
    
    # We'll run a simplified check:
    # The function should raise FileNotFoundError if data is missing (which it does in the impl)
    # We can't easily test the happy path without moving the whole data structure.
    # So we test the error condition or rely on the integration test flow.
    
    # Let's test the logic by mocking the file existence
    import os
    original_cwd = os.getcwd()
    os.chdir(str(setup_test_data))
    
    try:
        df = aggregate_results()
        assert isinstance(df, pd.DataFrame)
        assert 'config_id' in df.columns
        assert 'median_latency' in df.columns
        assert 'is_stable' in df.columns
        assert len(df) == 2
    finally:
        os.chdir(original_cwd)

def test_generate_final_pareto(setup_test_data):
    """Test that generate_final_pareto creates the output files."""
    import os
    original_cwd = os.getcwd()
    os.chdir(str(setup_test_data))
    
    try:
        df = aggregate_results()
        output_csv = setup_test_data / "data" / "results" / "aggregated.csv"
        output_png = setup_test_data / "data" / "results" / "pareto_frontier_final.png"
        
        generate_final_pareto(df, str(output_csv))
        
        assert output_csv.exists()
        assert output_png.exists()
        
        # Verify CSV content
        saved_df = pd.read_csv(output_csv)
        assert len(saved_df) == len(df)
    finally:
        os.chdir(original_cwd)
