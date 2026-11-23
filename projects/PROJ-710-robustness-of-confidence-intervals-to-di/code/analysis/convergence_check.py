"""
Convergence Check for Coverage Simulation.

This module verifies that the simulation has run for enough iterations
to achieve a standard error (SE) of the coverage rate below a target threshold (0.5%).
It reads the aggregated results from `artifacts/coverage_results.csv`.

Dependencies:
- T013a: Generates the raw simulation data.
- T013c: Produces `artifacts/coverage_results.csv` with columns including 'coverage_rate' and 'seed_count'.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
RESULTS_FILE = ARTIFACTS_DIR / "coverage_results.csv"
REPORT_FILE = ARTIFACTS_DIR / "convergence_report.json"

# Target threshold for Standard Error of coverage (0.5% = 0.005)
TARGET_SE_THRESHOLD = 0.005


def load_coverage_results(file_path: Path) -> pd.DataFrame:
    """
    Load the coverage results CSV.

    Args:
        file_path: Path to the coverage_results.csv file.

    Returns:
        DataFrame containing the simulation results.

    Raises:
        FileNotFoundError: If the results file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Results file not found at {file_path}. "
            "Did you run the main simulation (T013a/T042)?"
        )

    df = pd.read_csv(file_path)

    required_columns = ['dataset', 'epsilon', 'noise_type', 'statistic', 'coverage_rate', 'seed_count']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")

    if df.empty:
        raise ValueError(f"Results file {file_path} is empty. The simulation produced no data.")

    return df


def calculate_coverage_se(coverage_rate: float, n_simulations: int) -> float:
    """
    Calculate the Standard Error (SE) of a coverage proportion.

    The coverage rate is a proportion (p). The SE of a proportion is sqrt(p * (1-p) / n).
    Here, n_simulations corresponds to the number of independent trials (seeds) used
    to estimate that specific coverage_rate.

    Args:
        coverage_rate: The observed coverage proportion (0.0 to 1.0).
        n_simulations: The number of independent simulations (seeds) used.

    Returns:
        The calculated standard error.
    """
    if n_simulations <= 1:
        # If only 1 simulation, SE is undefined or 0 by convention in this context,
        # but practically it means we have no variance estimate.
        logger.warning(f"n_simulations is {n_simulations}. SE calculation may be unreliable.")
        return float('inf')

    p = coverage_rate
    if p < 0 or p > 1:
        raise ValueError(f"coverage_rate must be between 0 and 1, got {p}")

    se = np.sqrt((p * (1 - p)) / n_simulations)
    return se


def check_convergence(df: pd.DataFrame, target_se: float = TARGET_SE_THRESHOLD) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if the simulation has converged for all conditions.

    Convergence is achieved if the calculated SE for every condition is below the target threshold.
    The 'seed_count' column in the dataframe represents the number of simulations (n) used
    to derive the 'coverage_rate'.

    Args:
        df: DataFrame with coverage results.
        target_se: The maximum acceptable standard error.

    Returns:
        A tuple (is_converged, details_dict).
        details_dict contains per-condition SE calculations and an overall status.
    """
    results = []
    all_converged = True

    # Group by the unique condition keys to calculate SE for each aggregated result
    # Assuming the CSV is already aggregated by (dataset, epsilon, noise_type, statistic)
    # as per T013c specification.
    group_cols = ['dataset', 'epsilon', 'noise_type', 'statistic']

    for _, row in df.iterrows():
        coverage = row['coverage_rate']
        n_sims = row['seed_count']

        se = calculate_coverage_se(coverage, n_sims)
        is_ok = se <= target_se

        if not is_ok:
            all_converged = False

        results.append({
            "dataset": row['dataset'],
            "epsilon": row['epsilon'],
            "noise_type": row['noise_type'],
            "statistic": row['statistic'],
            "coverage_rate": coverage,
            "n_simulations": n_sims,
            "standard_error": se,
            "target_se": target_se,
            "converged": is_ok
        })

    return all_converged, {
        "conditions": results,
        "overall_converged": all_converged,
        "target_se": target_se
    }


def generate_convergence_report(details: Dict[str, Any], output_path: Path) -> None:
    """
    Generate a JSON report of the convergence analysis.

    Args:
        details: The dictionary returned by check_convergence.
        output_path: Path to save the JSON report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert numpy types to native python types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(i) for i in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    serializable_details = convert_numpy_types(details)

    with open(output_path, 'w') as f:
        json.dump(serializable_details, f, indent=2)

    logger.info(f"Convergence report saved to {output_path}")


def main() -> int:
    """
    Main entry point for the convergence check.

    1. Loads artifacts/coverage_results.csv.
    2. Calculates SE for each condition.
    3. Checks if SE < 0.005 for all conditions.
    4. Writes results to artifacts/convergence_report.json.
    5. Returns 0 if converged, 1 if not.
    """
    logger.info("Starting convergence check analysis.")

    try:
        # Load data
        df = load_coverage_results(RESULTS_FILE)
        logger.info(f"Loaded {len(df)} conditions from {RESULTS_FILE}")

        # Check convergence
        is_converged, details = check_convergence(df)

        # Generate report
        generate_convergence_report(details, REPORT_FILE)

        if is_converged:
            logger.info("SUCCESS: All conditions have converged (SE < 0.5%).")
            return 0
        else:
            logger.warning("FAILURE: One or more conditions have NOT converged (SE >= 0.5%).")
            # Log which ones failed
            failed_conditions = [c for c in details['conditions'] if not c['converged']]
            for cond in failed_conditions:
                logger.warning(
                    f"  - {cond['dataset']}/{cond['epsilon']}/{cond['noise_type']}/{cond['statistic']}: "
                    f"SE={cond['standard_error']:.6f} > {cond['target_se']}"
                )
            return 1

    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during convergence check: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())