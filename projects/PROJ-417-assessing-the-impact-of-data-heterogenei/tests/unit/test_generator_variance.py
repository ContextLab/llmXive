"""
Helper script to run the variance check and produce the artifact directly
without relying on pytest fixtures if needed, or as a standalone runner.
This ensures the artifact `data/results/test_variance_check.json` is produced
as required by the task.
"""
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
import numpy as np

# Add code to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from simulation.generator import (
    SimulationConfig,
    generate_synthetic_meta_analysis,
    validate_simulation_output,
)
from utils.logging import setup_logging

# Setup logging
setup_logging(level="INFO", log_file=None)

def create_temp_base_data():
    """Creates a temporary CSV file to act as the base data."""
    temp_dir = tempfile.mkdtemp()
    temp_csv = os.path.join(temp_dir, "base.csv")
    
    header = ["study_id", "effect_size", "se", "n_studies", "true_effect"]
    rows = []
    # Generate 50 studies
    for i in range(50):
        study_id = f"Study_{i}"
        eff = np.random.normal(0.3, 0.1)
        se = np.random.uniform(0.05, 0.2)
        n_studies = np.random.randint(10, 100)
        true_eff = 0.3
        rows.append([study_id, eff, se, n_studies, true_eff])
    
    with open(temp_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    return temp_csv

def run_variance_test():
    """
    Runs the variance check test and saves the result to data/results/test_variance_check.json
    """
    TARGET_TAU2 = 0.5
    NUM_REPLICATES = 500
    TOLERANCE = 0.01
    SEED = 42

    base_path = create_temp_base_data()
    
    config = SimulationConfig(
        tau2=TARGET_TAU2,
        num_replicates=NUM_REPLICATES,
        seed=SEED,
        base_data_path=base_path
    )
    
    print(f"Running generator with tau^2={TARGET_TAU2}, N={NUM_REPLICATES}")
    
    result = generate_synthetic_meta_analysis(config)
    validate_simulation_output(result)
    
    realized_variances = []
    
    for replicate in result.replicates:
        # Extract true_effects from the replicate
        # Assuming replicate is a list of objects/dicts with 'true_effect'
        true_effects = []
        for s in replicate:
            if hasattr(s, 'true_effect'):
                true_effects.append(s.true_effect)
            elif isinstance(s, dict) and 'true_effect' in s:
                true_effects.append(s['true_effect'])
        
        if len(true_effects) > 1:
            var_true = np.var(true_effects, ddof=1)
            realized_variances.append(var_true)
    
    if not realized_variances:
        raise ValueError("No valid replicates found.")
    
    mean_realized_var = np.mean(realized_variances)
    passed = abs(mean_realized_var - TARGET_TAU2) < TOLERANCE
    
    output_dir = project_root / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "test_variance_check.json"
    
    report = {
        "task_id": "T008",
        "target_tau2": TARGET_TAU2,
        "num_replicates": NUM_REPLICATES,
        "mean_realized_variance": float(mean_realized_var),
        "difference": float(abs(mean_realized_var - TARGET_TAU2)),
        "tolerance": TOLERANCE,
        "passed": passed,
        "seed": SEED
    }
    
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved to {output_path}")
    print(f"Test Result: {'PASSED' if passed else 'FAILED'}")
    print(f"Mean Realized Variance: {mean_realized_var:.4f}")
    print(f"Target: {TARGET_TAU2:.4f}")
    
    return passed

if __name__ == "__main__":
    success = run_variance_test()
    sys.exit(0 if success else 1)
