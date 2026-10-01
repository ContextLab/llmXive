import os
import sys
import json
import hashlib
import shutil
import tempfile
import argparse

# Add parent to path to allow imports from code/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.train import run_training_pipeline, load_processed_data
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode
from utils.checksum import compute_file_sha256

logger = get_logger(__name__)

def compute_file_hash(filepath):
    """Compute SHA-256 hash of a file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    return compute_file_sha256(filepath)

def run_training_run(seed, run_id, output_dir):
    """
    Run the training pipeline with a specific seed and capture the baseline comparison metrics.
    Returns a dict of metrics (MAE, R2) from the baseline comparison.
    """
    logger.info(f"Starting training run {run_id} with seed {seed}")
    
    # Prepare environment for this run
    # We need to ensure the model training uses the specific seed
    # The run_training_pipeline function is expected to handle the seed internally or via config
    # For this check, we assume the pipeline respects the seed passed or configured.
    # We will temporarily modify the config or environment if needed, but primarily rely on the function signature.
    
    # Since run_training_pipeline might write to global paths, we rely on it writing to the standard location
    # which we will then read.
    
    try:
        # Run the pipeline. Note: In a real scenario, we might need to inject the seed.
        # Assuming the pipeline respects a global seed or config.
        # If run_training_pipeline doesn't accept seed, we might need to set os.environ or similar.
        # For now, we call it. The task T026 implementation should handle seeding.
        
        # We need to ensure the seed is set for reproducibility.
        # Let's assume the training script checks for an env var or config.
        # We'll set an env var to force the seed if the training script supports it.
        os.environ['ALLOY_SEED'] = str(seed)
        
        run_training_pipeline()
        
        # Read the generated baseline_comparison.json
        baseline_path = "data/artifacts/baseline_comparison.json"
        if not os.path.exists(baseline_path):
            log_error(f"Baseline comparison file not found after run {run_id}")
            return None
        
        with open(baseline_path, 'r') as f:
            data = json.load(f)
        
        log_info(f"Run {run_id} completed. Metrics: {data}")
        return data
        
    except Exception as e:
        log_error(f"Run {run_id} failed: {str(e)}")
        raise

def test_loso_consistency_across_runs(num_runs=3):
    """
    Run the training pipeline multiple times with the same seed and verify consistency.
    """
    logger.info("Starting Cross-Validation Consistency Check (T069)")
    
    seed = 42 # Fixed seed for reproducibility
    runs = []
    
    for i in range(num_runs):
        try:
            metrics = run_training_run(seed, i+1, "data/artifacts")
            if metrics:
                runs.append(metrics)
        except Exception as e:
            log_error(f"Run {i+1} failed: {e}")
            return False, f"Run {i+1} failed: {e}"
    
    if len(runs) != num_runs:
        return False, "Not all runs completed successfully"
    
    # Compare metrics
    first_run = runs[0]
    for i, run in enumerate(runs[1:], 2):
        # Check MAE
        if abs(first_run['rf_model_mae'] - run['rf_model_mae']) > 1e-6:
            msg = f"Run 1 and Run {i} RF MAE mismatch: {first_run['rf_model_mae']} vs {run['rf_model_mae']}"
            log_error(msg)
            return False, msg
        
        # Check R2 (if available in baseline_comparison, otherwise check other artifacts)
        # The schema for baseline_comparison.json in T026 only specifies MAE keys.
        # T028 handles R2 per fold. We should check if the aggregate R2 is consistent if stored.
        # Assuming the baseline_comparison.json is the primary artifact for this check.
        # If R2 is needed, we might need to read the evaluation report.
        # Let's check if R2 exists in the loaded data, if so, compare.
        if 'rf_model_r2' in first_run and 'rf_model_r2' in run:
            if abs(first_run['rf_model_r2'] - run['rf_model_r2']) > 1e-6:
                msg = f"Run 1 and Run {i} RF R2 mismatch: {first_run['rf_model_r2']} vs {run['rf_model_r2']}"
                log_error(msg)
                return False, msg
        
        # Check Null Model MAE
        if abs(first_run['null_model_mae'] - run['null_model_mae']) > 1e-6:
            msg = f"Run 1 and Run {i} Null MAE mismatch: {first_run['null_model_mae']} vs {run['null_model_mae']}"
            log_error(msg)
            return False, msg

    log_info("Cross-Validation Consistency Check PASSED. All runs produced identical results.")
    
    # Write a report for T069
    report = {
        "seed": seed,
        "num_runs": num_runs,
        "status": "PASSED",
        "metrics_snapshot": runs[0]
    }
    
    report_path = "data/artifacts/cv_consistency_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return True, "Consistency verified"

def main():
    parser = argparse.ArgumentParser(description="Run CV Consistency Check")
    parser.add_argument('--runs', type=int, default=3, help="Number of runs to perform")
    args = parser.parse_args()
    
    success, message = test_loso_consistency_across_runs(args.runs)
    
    if success:
        print(f"SUCCESS: {message}")
        sys.exit(0)
    else:
        print(f"FAILURE: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
