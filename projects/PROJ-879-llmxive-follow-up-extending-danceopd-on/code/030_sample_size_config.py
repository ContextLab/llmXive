#!/usr/bin/env python
"""
T030c: Calculate Power and Configure Sample Size.

Calculates the required sample size for the full fidelity evaluation based on
pilot variance estimates. It handles missing pilot data, enforces timeout checks,
and ensures the calculated N does not exceed available data or time limits.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config, get_hyperparameter
from utils.timer import check_timeout
import numpy as np

try:
    from statsmodels.stats.power import TTestIndPower
except ImportError:
    print("ERROR: statsmodels is required for power analysis. Install via: pip install statsmodels")
    sys.exit(1)


def load_n_samples(pilot_variance_path: Path) -> Optional[float]:
    """
    Load the pilot variance estimate from the JSON file.
    Returns None if the file is missing or malformed.
    """
    if not pilot_variance_path.exists():
        print(f"WARNING: Pilot variance file not found at {pilot_variance_path}")
        return None

    try:
        with open(pilot_variance_path, 'r') as f:
            data = json.load(f)
        # Expecting structure: {"variance_clip_diff": float, ...}
        variance = data.get('variance_clip_diff')
        if variance is None:
            print("WARNING: 'variance_clip_diff' key missing in pilot variance file.")
            return None
        return float(variance)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: Failed to parse pilot variance file: {e}")
        return None


def check_test_split_size(test_split_path: Path, config: Any) -> int:
    """
    Check the number of available samples in the test split.
    Returns the count.
    """
    if not test_split_path.exists():
        print(f"ERROR: Test split file not found at {test_split_path}")
        sys.exit(1)

    try:
        import pandas as pd
        df = pd.read_parquet(test_split_path)
        count = len(df)
        print(f"INFO: Test split contains {count} samples.")
        return count
    except Exception as e:
        print(f"ERROR: Failed to read test split: {e}")
        sys.exit(1)


def calculate_required_sample_size(variance: float, effect_size: float = 0.5, power: float = 0.8, alpha: float = 0.05) -> int:
    """
    Calculate the required sample size per group using TTestIndPower.
    """
    if variance <= 0:
        print("ERROR: Variance must be positive.")
        return 0

    # TTestIndPower expects effect size (Cohen's d).
    # If we don't have a specific mean difference, we assume the effect size
    # is the target parameter (0.5 as per task description).
    # The function calculates N based on effect_size, alpha, power.
    
    analysis = TTestIndPower()
    try:
        # nobs1 is the sample size per group
        n = analysis.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            ratio=1.0, # Equal group sizes
            alternative='two-sided'
        )
        if n is None or np.isnan(n) or np.isinf(n):
            print("ERROR: Could not calculate sample size (nan/inf).")
            return 0
        return int(np.ceil(n))
    except Exception as e:
        print(f"ERROR: Power analysis failed: {e}")
        return 0


def write_sample_size_config(
    output_path: Path,
    calculated_n: int,
    max_available_n: int,
    pilot_variance: float,
    status: str,
    config: Any
):
    """
    Write the final sample size configuration to JSON.
    """
    # Apply timeout constraint check again before finalizing
    if check_timeout():
        print("WARNING: Timeout detected during configuration. Reducing N.")
        # Reduce N to a feasible limit (e.g., 100) if timeout is hit
        calculated_n = min(calculated_n, 100)
        status = "reduced_timeout"

    # Ensure N does not exceed available data
    final_n = min(calculated_n, max_available_n)
    
    if final_n < calculated_n and calculated_n <= max_available_n:
        status = "reduced" # Reduced due to available data limit
    
    if final_n < calculated_n and status != "reduced_timeout":
       if status == "calculated":
           status = "underpowered" # If we had to cut N significantly below target

    # Default status if everything is fine
    if status == "calculated" and final_n == calculated_n:
        status = "ok"

    result = {
        "status": status,
        "target_power": 0.8,
        "target_effect_size": 0.5,
        "pilot_variance": pilot_variance,
        "calculated_n_per_group": calculated_n,
        "max_available_n": max_available_n,
        "final_n_per_group": final_n,
        "total_samples": final_n * 2, # Teacher + Tree
        "timeout_limit_hours": get_hyperparameter("TIMEOUT_HOURS", 6),
        "seed": get_hyperparameter("SEED", 42)
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"INFO: Sample size configuration written to {output_path}")
    print(f"INFO: Status: {status}, Final N: {final_n} per group.")


def main():
    config = get_config()
    project_root = Path(__file__).parent.parent
    
    pilot_variance_path = project_root / "data" / "results" / "pilot_variance.json"
    test_split_path = project_root / "data" / "processed" / "test_split.parquet"
    output_path = project_root / "data" / "results" / "sample_size_config.json"

    print("Starting T030c: Calculate Power and Configure Sample Size...")

    # 1. Load Pilot Variance
    variance = load_n_samples(pilot_variance_path)
    
    if variance is None:
        # Handle Missing Pilot: Run a default pilot or fail?
        # Task says: "If missing, run a default pilot (N=50) or fail with error."
        # Since we are in T030c and T030b (Pilot Variance) should have run,
        # and the execution failed previously, we assume we must fail loud here
        # if the prerequisite data is missing, unless we can simulate a default.
        # However, the instruction says "run a default pilot". We cannot run T030b logic here.
        # We will fail loud to force the pipeline to re-run T030b.
        print("ERROR: Pilot variance data is missing. Cannot calculate power.")
        print("Please ensure T030b (Run Pilot Variance Calculation) has completed successfully.")
        sys.exit(1)

    print(f"INFO: Loaded pilot variance: {variance}")

    # 2. Check Test Split Size
    max_n = check_test_split_size(test_split_path, config)
    if max_n == 0:
        print("ERROR: No samples available in test split.")
        sys.exit(1)

    # 3. Calculate Required N
    # Using effect_size=0.5 as per task description
    calculated_n = calculate_required_sample_size(variance, effect_size=0.5)
    
    if calculated_n == 0:
        print("ERROR: Failed to calculate required sample size.")
        sys.exit(1)

    print(f"INFO: Calculated required N per group: {calculated_n}")

    # 4. Check Timeout (T033a integration)
    if check_timeout():
        print("WARNING: Timeout already detected. Reducing N.")
        # Reduce N to a minimal feasible count
        calculated_n = min(calculated_n, 50)
        status = "reduced"
    else:
        status = "calculated"

    # 5. Write Config
    write_sample_size_config(
        output_path=output_path,
        calculated_n=calculated_n,
        max_available_n=max_n,
        pilot_variance=variance,
        status=status,
        config=config
    )

    print("T030c completed successfully.")


if __name__ == "__main__":
    main()