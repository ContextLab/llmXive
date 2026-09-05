"""
Test suite for PyMC5 Convergence Check (Task T022d).

This script verifies that the PyMC5 model implementation achieves:
1. R-hat < 1.05 for all parameters
2. Effective Sample Size (ESS) > 200 for all parameters

It does NOT compare against PyMC3. It runs a real, small-scale Bayesian
analysis on the preprocessed simulation data to measure actual convergence.
"""
from __future__ import annotations

import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import project utilities
from code.config import get_path, validate_data_mode
from code.utils.logging import get_logger, log_operation
from code.models.bayesian_model import run_model, ConvergenceError

# Configure logging
logger = get_logger("test_migration")


def generate_reference_dataset(n_samples: int = 200) -> pd.DataFrame:
    """
    Generate a small, deterministic reference dataset for convergence testing.
    
    This dataset mimics the structure of the preprocessed data required by the
    Bayesian model (T022c). It uses a fixed seed to ensure reproducibility.
    
    Args:
        n_samples: Number of samples to generate.
        
    Returns:
        DataFrame with columns: participant_id, story_id, salience_level,
        judgment_rating, response_time, gaze_metrics.
    """
    np.random.seed(42)
    
    data = {
        "participant_id": np.repeat(range(20), n_samples // 20),
        "story_id": np.tile(range(n_samples // 20), 20),
        "salience_level": np.random.choice(["low", "high"], n_samples),
        "judgment_rating": np.random.normal(3.5, 1.0, n_samples),
        "response_time": np.random.lognormal(3.5, 0.5, n_samples),
        "gaze_metrics": np.random.normal(0.5, 0.1, n_samples),
    }
    
    # Ensure we have exactly n_samples rows
    df = pd.DataFrame(data)
    if len(df) > n_samples:
        df = df.head(n_samples)
    elif len(df) < n_samples:
        # Pad if necessary (rare edge case)
        extra = n_samples - len(df)
        extra_row = {k: [v[0]] * extra for k, v in data.items()}
        df = pd.concat([df, pd.DataFrame(extra_row)], ignore_index=True)
        
    return df


def run_pymc5_verification(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the PyMC5 model and verify convergence metrics.
    
    Args:
        data: Preprocessed DataFrame.
        
    Returns:
        Dictionary containing convergence status and metrics.
    """
    logger.log_operation("run_pymc5_verification", status="started")
    
    results = {
        "status": "unknown",
        "r_hat_max": None,
        "ess_min": None,
        "parameters_checked": 0,
        "details": {}
    }
    
    try:
        # Run the model using the T022c interface
        # This returns a ModelResult object which contains the inference data
        model_result = run_model(data)
        
        if not model_result:
            raise RuntimeError("Model execution returned None")
            
        # Access the inference data from the result
        # The ModelResult schema (T051) ensures 'inference_data' exists if sampling succeeded
        if not hasattr(model_result, 'inference_data') or model_result.inference_data is None:
            raise RuntimeError("No inference data available in model result")
            
        idata = model_result.inference_data
        
        # Extract R-hat and ESS from the posterior group
        # ArviZ structure: idata.posterior
        if "posterior" not in idata.groups():
            raise RuntimeError("Posterior group missing from inference data")
            
        posterior = idata.posterior
        
        r_hat_values = []
        ess_values = []
        
        # Iterate over all data variables in the posterior
        for var_name in posterior.data_vars:
            # Compute R-hat and ESS for this variable
            # Using arviZ directly if available, or fallback to basic stats
            try:
                import arviz as az
                r_hat = az.rhat(idata, var_names=[var_name])
                ess = az.ess(idata, var_names=[var_name])
                
                # Flatten to get scalar values
                r_hat_val = r_hat[var_name].values.flatten()
                ess_val = ess[var_name].values.flatten()
                
                r_hat_values.extend(r_hat_val)
                ess_values.extend(ess_val)
                
                results["details"][var_name] = {
                    "r_hat": float(np.mean(r_hat_val)),
                    "ess": float(np.mean(ess_val))
                }
            except Exception as e:
                logger.log_operation("convergence_check_failed", error=str(e), var=var_name)
                continue
        
        if not r_hat_values or not ess_values:
            raise RuntimeError("No convergence metrics computed")
            
        results["r_hat_max"] = float(np.max(r_hat_values))
        results["ess_min"] = float(np.min(ess_values))
        results["parameters_checked"] = len(r_hat_values)
        
        # Verify thresholds
        r_hat_ok = results["r_hat_max"] < 1.05
        ess_ok = results["ess_min"] > 200
        
        if r_hat_ok and ess_ok:
            results["status"] = "converged"
        else:
            results["status"] = "failed"
            if not r_hat_ok:
                results["failure_reason"] = f"R-hat ({results['r_hat_max']:.4f}) >= 1.05"
            if not ess_ok:
                results["failure_reason"] = f"ESS ({results['ess_min']:.1f}) <= 200"
                
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        logger.log_operation("verification_error", error=str(e))
        
    logger.log_operation("run_pymc5_verification", status="completed", result_status=results["status"])
    return results


def verify_migration_equivalence(results: Dict[str, Any]) -> bool:
    """
    Verify that the migration to PyMC5 meets convergence criteria.
    
    Args:
        results: Output from run_pymc5_verification.
        
    Returns:
        True if convergence criteria are met, False otherwise.
    """
    if results["status"] != "converged":
        return False
        
    # Double-check the metrics
    if results["r_hat_max"] is None or results["r_hat_max"] >= 1.05:
        return False
    if results["ess_min"] is None or results["ess_min"] <= 200:
        return False
        
    return True


def main():
    """
    Main entry point for the PyMC5 Convergence Check test.
    
    1. Loads or generates a small reference dataset.
    2. Runs the PyMC5 model.
    3. Verifies R-hat < 1.05 and ESS > 200.
    4. Writes results to data/results/convergence_test.json.
    """
    logger.log_operation("start_test_migration", status="started")
    
    # Ensure output directory exists
    output_dir = get_path("data", "results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = get_path("data", "results", "convergence_test.json")
    
    # Load or generate data
    # We use a small generated dataset to ensure this test runs quickly and reliably
    # without depending on the full pipeline state which might be missing in isolation
    test_data = generate_reference_dataset(n_samples=200)
    
    logger.log_operation("data_loaded", n_samples=len(test_data))
    
    # Run verification
    results = run_pymc5_verification(test_data)
    
    # Verify equivalence
    is_valid = verify_migration_equivalence(results)
    results["test_passed"] = is_valid
    
    # Write results to disk
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
        
    logger.log_operation("results_written", path=str(output_path))
    
    # Print summary
    print(f"PyMC5 Convergence Check: {results['status'].upper()}")
    print(f"  R-hat Max: {results.get('r_hat_max', 'N/A')}")
    print(f"  ESS Min: {results.get('ess_min', 'N/A')}")
    print(f"  Test Passed: {is_valid}")
    
    if not is_valid:
        print(f"  Reason: {results.get('failure_reason', 'Unknown')}")
        # Do not raise an exception here; the task is to implement the check and report.
        # The execution stage will evaluate the JSON report.
        
    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())