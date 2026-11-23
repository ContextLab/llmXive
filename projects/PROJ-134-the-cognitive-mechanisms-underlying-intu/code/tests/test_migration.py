"""
PyMC5 Convergence Check and Migration Verification.

This script implements T022d: Verifies R-hat < 1.05 and effective sample size > 200
for all parameters in the PyMC5 model. It does NOT compare against PyMC3.

It also includes a reference dataset generator for migration equivalence testing
(T022c dependency).
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import the model interface defined in T022b/T022c
# These names are guaranteed to exist in code/models/bayesian_model.py
from code.models.bayesian_model import build_model, run_model, ConvergenceError, ModelResult
from code.config import get_path

# Suppress ArviZ/Pymc warnings for cleaner output during verification
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Constants
R_HAT_THRESHOLD = 1.05
ESS_THRESHOLD = 200
CONVERGENCE_CHECK_FILE = "data/results/convergence_check.json"


def generate_reference_dataset(n_samples: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Generates a small, deterministic reference dataset for migration testing.
    This ensures we have real data to run the model against without depending
    on the full pipeline ingestion (which may be broken in other tasks).

    The data mimics the structure expected by the Bayesian model:
    - participant_id
    - salience_level (0 or 1)
    - judgment_rating (continuous)
    """
    rng = np.random.default_rng(seed)
    participants = rng.integers(0, 20, size=n_samples)
    salience = rng.integers(0, 2, size=n_samples).astype(float)

    # Simulate a simple relationship: rating ~ 0.5 * salience + noise
    # This ensures the model has something to converge on.
    noise = rng.normal(0, 0.5, size=n_samples)
    ratings = 2.0 + 0.5 * salience + noise

    df = pd.DataFrame({
        "participant_id": participants,
        "salience_level": salience,
        "judgment_rating": ratings
    })
    return df


def run_pymc5_verification(data: Optional[pd.DataFrame] = None) -> Tuple[ModelResult, Dict[str, Any]]:
    """
    Runs the PyMC5 model on the provided data (or generated reference data)
    and performs convergence checks.

    Returns:
        Tuple of (ModelResult object, Dictionary of convergence metrics)
    """
    if data is None:
        print("No data provided. Generating reference dataset for verification.")
        data = generate_reference_dataset(n_samples=100)

    # Prepare data for the model
    # The model expects a dictionary with specific keys
    model_data = {
        "y": data["judgment_rating"].values,
        "x": data["salience_level"].values,
        "n_participants": data["participant_id"].nunique()
    }

    print(f"Running PyMC5 model with {len(data)} samples...")
    try:
        # Run the model (this calls pm.sample internally)
        # We use a small number of draws and chains for speed in verification
        result = run_model(model_data, draws=500, chains=2, target_accept=0.9)
    except Exception as e:
        print(f"Model execution failed: {e}")
        # If the model fails to run, we cannot check convergence.
        # We raise a specific error to be caught by the main entry point.
        raise RuntimeError(f"Model execution failed: {e}") from e

    # Extract convergence metrics from the result
    # The ModelResult object contains 'r_hat' and 'effective_sample_size'
    # We assume these are dictionaries mapping parameter names to values
    metrics = {
        "r_hat": result.r_hat,
        "effective_sample_size": result.effective_sample_size,
        "is_inconclusive": result.is_inconclusive
    }

    return result, metrics


def verify_migration_equivalence(metrics: Dict[str, Any]) -> bool:
    """
    Verifies that the migration to PyMC5 produced convergent results.
    Specifically checks R-hat < 1.05 and ESS > 200 for all parameters.

    Returns:
        True if all checks pass, False otherwise.
    """
    all_passed = True
    details = []

    r_hat_dict = metrics.get("r_hat", {})
    ess_dict = metrics.get("effective_sample_size", {})

    # Check R-hat
    for param, val in r_hat_dict.items():
        if val >= R_HAT_THRESHOLD:
            details.append(f"FAIL: R-hat for {param} is {val:.4f} (threshold: {R_HAT_THRESHOLD})")
            all_passed = False
        else:
            details.append(f"PASS: R-hat for {param} is {val:.4f}")

    # Check ESS
    for param, val in ess_dict.items():
        if val <= ESS_THRESHOLD:
            details.append(f"FAIL: ESS for {param} is {val:.2f} (threshold: {ESS_THRESHOLD})")
            all_passed = False
        else:
            details.append(f"PASS: ESS for {param} is {val:.2f}")

    print("\n--- Convergence Verification Report ---")
    for line in details:
        print(line)
    print("---------------------------------------")

    return all_passed


def save_convergence_report(metrics: Dict[str, Any], passed: bool, output_path: str) -> None:
    """
    Saves the convergence check results to a JSON file.
    """
    report = {
        "status": "passed" if passed else "failed",
        "thresholds": {
            "r_hat": R_HAT_THRESHOLD,
            "ess": ESS_THRESHOLD
        },
        "metrics": metrics,
        "details": [
            f"R-hat check: {'PASS' if all(v < R_HAT_THRESHOLD for v in metrics['r_hat'].values()) else 'FAIL'}",
            f"ESS check: {'PASS' if all(v > ESS_THRESHOLD for v in metrics['effective_sample_size'].values()) else 'FAIL'}"
        ]
    }

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Convergence report saved to: {output_path}")


def main() -> int:
    """
    Main entry point for T022d.
    1. Loads or generates data.
    2. Runs the PyMC5 model.
    3. Verifies convergence (R-hat, ESS).
    4. Writes the report to data/results/convergence_check.json.
    """
    print("Starting PyMC5 Convergence Check (T022d)...")

    try:
        # 1. Prepare Data
        # We generate reference data if none is provided to ensure this script
        # can run independently of the potentially broken ingestion pipeline.
        # In a full pipeline, this would load from data/processed/...
        data = generate_reference_dataset(n_samples=100, seed=42)

        # 2. Run Model
        result, metrics = run_pymc5_verification(data)

        # 3. Verify Convergence
        passed = verify_migration_equivalence(metrics)

        # 4. Save Report
        output_path = str(get_path(CONVERGENCE_CHECK_FILE))
        save_convergence_report(metrics, passed, output_path)

        if passed:
            print("\n✓ All convergence checks passed.")
            return 0
        else:
            print("\n✗ Convergence checks failed.")
            return 1

    except RuntimeError as e:
        print(f"\n✗ Verification failed with error: {e}")
        # Write a failure report so downstream tasks know what happened
        output_path = str(get_path(CONVERGENCE_CHECK_FILE))
        save_convergence_report({"error": str(e)}, False, output_path)
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())