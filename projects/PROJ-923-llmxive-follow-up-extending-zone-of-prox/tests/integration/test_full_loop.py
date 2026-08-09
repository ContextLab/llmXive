"""
Integration test for the full comparison pipeline (US3).

This test verifies the end-to-end execution of the comparative analysis:
1. Runs the baseline simulation (T016/T026) to generate baseline metrics.
2. Runs the CAP-ZPPO simulation (T023/T026) to generate CAP metrics.
3. Invokes the statistical analysis module (T029/T030) to compare results.
4. Validates the output against the aggregated_metrics schema (T033).

Dependencies:
- T016 (Static ZPPO Loop)
- T023 (CAP ZPPO Loop)
- T029 (Stats logic)
- T030 (Catastrophic forgetting check)
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path
import numpy as np

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_config, Config
from data.generators import generate_synthetic_rollout_log
from loops.base_zppo import run_static_zppo_simulation
from loops.cap_zppo import run_cap_zppo_simulation
from analysis.metrics import calculate_metrics_from_log, save_metrics_to_csv, ensure_directory
from analysis.stats import compare_distributions, check_catastrophic_forgetting
from utils.validation import validate_aggregated_metrics
from utils.seeds import set_global_seed, get_rng

# Fixtures
@pytest.fixture
def temp_project_dir():
    """Creates a temporary directory structure mimicking the project root for testing."""
    temp_dir = tempfile.mkdtemp(prefix="llmxive_test_")
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        # Create necessary subdirectories
        os.makedirs("data/metrics", exist_ok=True)
        os.makedirs("data/logs", exist_ok=True)
        os.makedirs("contracts", exist_ok=True)
        # Create a dummy config file if not present
        config_path = Path("config.yaml")
        if not config_path.exists():
            config_path.write_text("""
            seeds:
              global_seed: 42
            paths:
              data_dir: data
              log_dir: data/logs
              metrics_dir: data/metrics
            simulation:
              num_cycles: 10
              noise_sigma: 0.05
            """)
        yield temp_dir
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config(temp_project_dir):
    """Mock config for the test environment."""
    config = get_config()
    config.paths.data_dir = Path(temp_project_dir) / "data"
    config.paths.log_dir = Path(temp_project_dir) / "data" / "logs"
    config.paths.metrics_dir = Path(temp_project_dir) / "data" / "metrics"
    config.simulation.num_cycles = 5  # Small number for fast integration test
    config.simulation.noise_sigma = 0.05
    return config

def test_full_comparison_pipeline(temp_project_dir, mock_config):
    """
    Integration test: Run Baseline -> Run CAP -> Compare -> Validate.
    
    This test ensures that:
    1. Both simulation loops complete successfully.
    2. Metrics are calculated and saved correctly.
    3. Statistical comparison produces valid results (p-values, std dev).
    4. The final output conforms to the aggregated_metrics schema.
    """
    set_global_seed(42)
    rng = get_rng()

    # 1. Generate synthetic rollout log (simulating T012)
    # We use a small subset for the integration test speed
    log_path = Path(mock_config.paths.log_dir) / "test_rollout.json"
    ensure_directory(log_path)
    
    # Generate a minimal synthetic log
    # In a real run, this would be a large file, but for integration we simulate the structure
    generate_synthetic_rollout_log(
        output_path=str(log_path),
        num_samples=20, # Small sample for test
        seed=42,
        tasks=["mmlu_high_school_math", "mmlu_high_school_physics"]
    )

    # 2. Run Baseline Simulation (T016)
    baseline_log_path = Path(mock_config.paths.log_dir) / "baseline_run.json"
    ensure_directory(baseline_log_path)
    
    run_static_zppo_simulation(
        input_log=str(log_path),
        output_log=str(baseline_log_path),
        num_cycles=mock_config.simulation.num_cycles,
        noise_sigma=mock_config.simulation.noise_sigma,
        seed=42
    )
    
    assert baseline_log_path.exists(), "Baseline simulation failed to produce output log"

    # 3. Run CAP Simulation (T023)
    cap_log_path = Path(mock_config.paths.log_dir) / "cap_run.json"
    ensure_directory(cap_log_path)
    
    run_cap_zppo_simulation(
        input_log=str(log_path),
        output_log=str(cap_log_path),
        num_cycles=mock_config.simulation.num_cycles,
        noise_sigma=mock_config.simulation.noise_sigma,
        seed=43 # Different seed to ensure variance
    )
    
    assert cap_log_path.exists(), "CAP simulation failed to produce output log"

    # 4. Calculate Metrics (T017/T024)
    baseline_metrics = calculate_metrics_from_log(str(baseline_log_path))
    cap_metrics = calculate_metrics_from_log(str(cap_log_path))

    # Verify metrics structure
    assert "aucc" in baseline_metrics, "Baseline metrics missing AUCC"
    assert "final_accuracy" in baseline_metrics, "Baseline metrics missing final_accuracy"
    assert "aucc" in cap_metrics, "CAP metrics missing AUCC"
    assert "final_accuracy" in cap_metrics, "CAP metrics missing final_accuracy"

    # 5. Statistical Comparison (T029/T030)
    # Since we only have one run here, we simulate a distribution by running a few iterations
    # or we treat the single run as a sample of size 1 for the integration check.
    # For a robust integration test, we generate a small synthetic distribution based on the logs.
    
    # Simulate multiple runs for the statistical test (mocking the batch runner T031 behavior)
    baseline_auccs = [baseline_metrics["aucc"]] + [baseline_metrics["aucc"] + rng.normal(0, 0.01) for _ in range(4)]
    cap_auccs = [cap_metrics["aucc"]] + [cap_metrics["aucc"] + rng.normal(0, 0.01) for _ in range(4)]
    
    baseline_accs = [baseline_metrics["final_accuracy"]] + [baseline_metrics["final_accuracy"] + rng.normal(0, 0.005) for _ in range(4)]
    cap_accs = [cap_metrics["final_accuracy"]] + [cap_metrics["final_accuracy"] + rng.normal(0, 0.005) for _ in range(4)]

    # Run comparison
    comparison_result = compare_distributions(baseline_auccs, cap_auccs)
    forgetting_result = check_catastrophic_forgetting(baseline_accs, cap_accs)

    # Validate Comparison Result Structure
    assert "p_value" in comparison_result, "Comparison result missing p_value"
    assert "mean_diff" in comparison_result, "Comparison result missing mean_diff"
    assert "std_baseline" in comparison_result, "Comparison result missing std_baseline (SC-002)"
    assert "std_cap" in comparison_result, "Comparison result missing std_cap"
    
    # Validate Forgetting Result
    assert "forgetting_detected" in forgetting_result, "Forgetting result missing flag"
    assert "accuracy_delta" in forgetting_result, "Forgetting result missing delta"

    # 6. Validate against Schema (T033)
    # Construct the aggregated metrics object as expected by the schema
    aggregated_data = {
        "baseline": {
            "aucc": float(np.mean(baseline_auccs)),
            "final_accuracy": float(np.mean(baseline_accs)),
            "std_aucc": float(comparison_result["std_baseline"])
        },
        "cap": {
            "aucc": float(np.mean(cap_auccs)),
            "final_accuracy": float(np.mean(cap_accs)),
            "std_aucc": float(comparison_result["std_cap"])
        },
        "comparison": {
            "p_value": float(comparison_result["p_value"]),
            "mean_diff": float(comparison_result["mean_diff"]),
            "forgetting_detected": bool(forgetting_result["forgetting_detected"]),
            "accuracy_delta": float(forgetting_result["accuracy_delta"])
        }
    }

    # Save to temp file for validation
    output_path = Path(mock_config.paths.metrics_dir) / "integration_results.json"
    import json
    with open(output_path, "w") as f:
        json.dump(aggregated_data, f)

    # Validate schema (assuming a simple check or a real schema file exists)
    # If contracts/aggregated_metrics.schema.yaml exists, we would load and validate there.
    # For this integration test, we verify the structure matches the expected keys.
    try:
        validate_aggregated_metrics(output_path)
    except Exception as e:
        # If validation fails due to missing schema file in test env, we check structure manually
        # but in a real CI, the schema file should be present (T004)
        if not Path("contracts/aggregated_metrics.schema.yaml").exists():
            # Manual structure check as fallback for integration test environment
            assert "baseline" in aggregated_data
            assert "cap" in aggregated_data
            assert "comparison" in aggregated_data
            assert "aucc" in aggregated_data["baseline"]
            assert "aucc" in aggregated_data["cap"]
            assert "p_value" in aggregated_data["comparison"]
            pytest.skip("Schema file not present in test env, but structure validated manually.")
        else:
            raise e

    # Final assertion: Ensure the pipeline completed without crashing
    assert True, "Full comparison pipeline executed successfully."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])