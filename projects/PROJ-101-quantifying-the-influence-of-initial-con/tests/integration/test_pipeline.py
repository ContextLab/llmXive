"""
Integration test for the full chaotic system analysis pipeline.

This test verifies:
1. End-to-end execution of the generation, baseline, FTLE, and regression pipeline.
2. Correctness of outputs (files exist, schema valid).
3. Performance constraint: total runtime <= 30s for N=5, restricted noise levels.

Addresses US-1 Acceptance Scenario 3.
"""
import os
import sys
import json
import time
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"

sys.path.insert(0, str(PROJECT_ROOT))

from config import get_full_config, set_simulation_seed, set_noise_levels, set_N_oscillators
from data.generator import generate_batch_trajectories, UnphysicalTrajectoryError
from data.loader import save_trajectory
from analysis.baseline import compute_asymptotic_baseline, save_baseline_result, load_baseline_result, validate_and_gate_for_baseline, NonChaoticSystemError
from analysis.ftle import run_sliding_window_sweep, save_ftle_results
from analysis.regression import run_full_regression_analysis, validate_trial_counts

# Configuration for the integration test (Optimized for speed <= 30s)
TEST_CONFIG = {
    "N": 5,
    "noise_levels": [0.001, 0.01],  # Reduced range to ensure speed
    "time_steps": 100,  # Short trajectory for speed
    "t_max": 10.0,
    "num_trials": 3,  # Minimal trials for validation
    "rtol": 1e-6,  # Relaxed tolerances for speed
    "atol": 1e-9,
    "seed": 42
}

def setup_module(module):
    """Ensure data directories exist."""
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)

def test_full_pipeline_execution():
    """
    Run the full pipeline: Generation -> Baseline -> FTLE -> Regression.
    Verify runtime <= 30s and all output artifacts are valid.
    """
    start_time = time.time()
    
    # 1. Setup Config
    set_simulation_seed(TEST_CONFIG["seed"])
    set_N_oscillators(TEST_CONFIG["N"])
    set_noise_levels(TEST_CONFIG["noise_levels"])
    
    config = get_full_config()
    config.numerical.rtol = TEST_CONFIG["rtol"]
    config.numerical.atol = TEST_CONFIG["atol"]
    
    # 2. Generate Trajectories (US1)
    # We manually generate a few short trajectories to avoid the full T018 loop
    # but ensure the logic path is identical.
    generated_files = []
    for sigma in TEST_CONFIG["noise_levels"]:
        for t_idx in range(TEST_CONFIG["num_trials"]):
            try:
                # Generate trajectory
                traj_data = generate_batch_trajectories(
                    N=TEST_CONFIG["N"],
                    sigma_noise=sigma,
                    t_max=TEST_CONFIG["t_max"],
                    num_points=TEST_CONFIG["time_steps"],
                    seed=config.simulation.seed + t_idx
                )[0] # Take first of batch (batch size 1 here)
                
                # Save
                filename = f"test_trajectory_N{TEST_CONFIG['N']}_sigma{sigma:.3f}_trial{t_idx}.csv"
                filepath = DATA_DIR / "raw" / filename
                save_trajectory(traj_data, str(filepath))
                generated_files.append(str(filepath))
            except UnphysicalTrajectoryError as e:
                # Expected for high noise or divergence, skip this specific trial
                continue

    assert len(generated_files) > 0, "No valid trajectories generated for test."

    # 3. Compute Baseline (US2)
    # Compute baseline for clean system (sigma=0)
    baseline_data = compute_asymptotic_baseline(
        N=TEST_CONFIG["N"],
        t_max=TEST_CONFIG["t_max"],
        num_points=TEST_CONFIG["time_steps"]
    )
    
    baseline_file = DATA_DIR / "processed" / f"baseline_{TEST_CONFIG['N']}.json"
    save_baseline_result(baseline_data, str(baseline_file))
    
    # Validate and Gate
    try:
        validate_and_gate_for_baseline(baseline_data)
    except NonChaoticSystemError:
        pytest.fail("Baseline validation failed: System detected as non-chaotic.")

    # 4. Compute FTLE (US2)
    # Run sweep on generated files
    sweep_results = run_sliding_window_sweep(
        trajectory_files=generated_files,
        baseline_lambda_max=baseline_data["lambda_max"],
        window_sizes=[50, 100] # Small windows for speed
    )
    
    ftle_file = DATA_DIR / "processed" / "ftle_sweep.json"
    save_ftle_results(sweep_results, str(ftle_file))
    
    # 5. Regression Analysis (US3)
    # Run full analysis
    regression_results = run_full_regression_analysis(
        ftle_sweep_path=str(ftle_file),
        baseline_path=str(baseline_file),
        output_dir=str(DATA_DIR / "processed")
    )
    
    # 6. Verify Outputs
    assert (DATA_DIR / "processed" / "results.json").exists(), "Regression results missing."
    assert (DATA_DIR / "processed" / "plot_deviation_vs_noise.png").exists(), "Deviation plot missing."
    assert (DATA_DIR / "processed" / "plot_convergence.png").exists(), "Convergence plot missing."
    
    # Verify JSON content
    with open(DATA_DIR / "processed" / "results.json") as f:
        results = json.load(f)
        assert "p_value_model" in results, "Missing p_value_model in results."
        assert "effect_size_model" in results, "Missing effect_size_model in results."
    
    end_time = time.time()
    duration = end_time - start_time
    
    # 7. Performance Check
    assert duration <= 30.0, f"Pipeline execution took {duration:.2f}s, exceeding 30s limit."
    
    print(f"Integration test passed. Total runtime: {duration:.2f}s")

def test_pipeline_cli_execution():
    """
    Test running the pipeline via CLI (if main.py is invoked directly).
    This ensures the CLI entry point works correctly.
    """
    # This test is a placeholder for CLI validation if T037a is invoked via CLI.
    # For now, we verify the script structure exists.
    main_py = CODE_DIR / "main.py"
    assert main_py.exists(), "main.py not found"
    
    # We could invoke: python code/main.py --N 5 --noise-levels 0.001 0.01 --max-time 10
    # But for speed, we rely on the function-level test above which covers the logic.
    pass