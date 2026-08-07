"""
Sensitivity Analysis Module for P-Value Validity Study.

Implements the sensitivity sweep over discrete correlation thresholds (rho)
to quantify how KS statistics vary as a function of correlation strength.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

# Import from project utilities
from utils.exceptions import AnalysisError
from utils.simulation import SimulationConfig

# Import from sibling modules in code/
from analyze_pvalues import calculate_ks_statistic
from bootstrap_ci import load_trajectory_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_trajectories_for_rho(
    trajectories_dir: Path,
    rho: float,
    seed: Optional[int] = None
) -> List[np.ndarray]:
    """
    Load all p-value trajectories for a specific correlation threshold (rho).

    Args:
        trajectories_dir: Path to the directory containing trajectory JSON files.
        rho: The correlation threshold to filter by.
        seed: Optional specific seed to load. If None, loads all matching rho.

    Returns:
        List of 1D numpy arrays, each containing p-values from one iteration.

    Raises:
        AnalysisError: If no trajectories are found for the given rho.
    """
    if not trajectories_dir.exists():
        raise AnalysisError(f"Trajectories directory not found: {trajectories_dir}")

    trajectories = []
    found_count = 0

    for json_file in trajectories_dir.glob("*.json"):
        try:
            data = load_trajectory_data(json_file)
            if data is None:
                continue

            # Check metadata for matching rho
            meta = data.get("metadata", {})
            file_rho = meta.get("rho")

            # Handle float comparison with tolerance
            if file_rho is not None and abs(float(file_rho) - float(rho)) < 1e-6:
                if seed is not None and meta.get("seed") != seed:
                    continue

                # Extract p-values (assuming 'pvalues' key exists)
                pvals = data.get("pvalues")
                if pvals and isinstance(pvals, list):
                    trajectories.append(np.array(pvals))
                    found_count += 1
                    logger.debug(f"Loaded trajectory from {json_file.name} (rho={rho})")

        except Exception as e:
            logger.warning(f"Failed to load {json_file}: {e}")
            continue

    if found_count == 0:
        raise AnalysisError(f"No trajectories found for rho={rho} in {trajectories_dir}")

    logger.info(f"Loaded {found_count} trajectories for rho={rho}")
    return trajectories

def calculate_ks_statistic_for_rho(
    trajectories: List[np.ndarray],
    permutation_reference: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Calculate the KS statistic for a set of trajectories at a specific rho.

    If a permutation reference is provided, compares against that.
    Otherwise, compares against the theoretical Uniform(0,1) distribution.

    Args:
        trajectories: List of p-value arrays (one per iteration).
        permutation_reference: Optional array of p-values from a permutation test.

    Returns:
        Dictionary containing:
            - 'KS_statistic': float
            - 'p_value': float (if comparing to uniform)
            - 'n_samples': int (total p-values analyzed)
            - 'method': str ('uniform' or 'permutation')
    """
    if not trajectories:
        raise AnalysisError("Cannot calculate KS statistic: no trajectories provided")

    # Concatenate all p-values from all iterations
    all_pvalues = np.concatenate(trajectories)
    n_samples = len(all_pvalues)

    if permutation_reference is not None:
        # Compare against permutation reference empirical CDF
        # Sort both for KS calculation
        sorted_sample = np.sort(all_pvalues)
        sorted_ref = np.sort(permutation_reference)

        # Calculate empirical CDFs at the sample points
        # For KS, we look at max difference between CDFs
        # scipy.stats.ks_2samp handles this directly
        ks_result = stats.ks_2samp(all_pvalues, permutation_reference)
        ks_stat = ks_result.statistic
        p_val = ks_result.pvalue
        method = "permutation"
    else:
        # Compare against theoretical Uniform(0,1)
        # scipy.stats.kstest with 'uniform' tests against U(0,1)
        ks_result = stats.kstest(all_pvalues, 'uniform')
        ks_stat = ks_result.statistic
        p_val = ks_result.pvalue
        method = "uniform"

    return {
        "KS_statistic": float(ks_stat),
        "p_value": float(p_val),
        "n_samples": n_samples,
        "method": method
    }

def run_sensitivity_analysis(
    trajectories_dir: Path,
    output_path: Path,
    rho_values: List[float] = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9],
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full sensitivity analysis sweep over discrete rho values.

    This implements FR-007: Sensitivity analysis sweep for discrete rho.

    Args:
        trajectories_dir: Path to directory with trajectory JSON files.
        output_path: Path where the results JSON will be written.
        rho_values: List of correlation thresholds to sweep.
        seed: Optional seed to filter trajectories.

    Returns:
        Dictionary containing the full sensitivity analysis results.
    """
    logger.info(f"Starting sensitivity analysis sweep for rho: {rho_values}")

    results = {
        "sweep_parameters": {
            "rho_values": rho_values,
            "seed": seed,
            "trajectories_dir": str(trajectories_dir)
        },
        "sensitivity_results": []
    }

    # Optional: Load a permutation reference if available (e.g., from rho=0)
    # For this implementation, we compare each rho against the theoretical uniform
    # as the primary baseline, as specified in the task description context.
    permutation_ref = None

    for rho in rho_values:
        logger.info(f"Processing rho={rho}...")

        try:
            # Load trajectories for this rho
            trajectories = load_trajectories_for_rho(trajectories_dir, rho, seed)

            # Calculate KS statistic
            ks_result = calculate_ks_statistic_for_rho(trajectories, permutation_ref)

            # Add rho to the result
            ks_result["rho"] = float(rho)

            results["sensitivity_results"].append(ks_result)

            logger.info(
                f"  rho={rho}: KS={ks_result['KS_statistic']:.4f}, "
                f"p={ks_result['p_value']:.4f}, n={ks_result['n_samples']}"
            )

        except AnalysisError as e:
            logger.error(f"Failed to process rho={rho}: {e}")
            results["sensitivity_results"].append({
                "rho": float(rho),
                "error": str(e),
                "KS_statistic": None,
                "p_value": None
            })

    # Write results to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
    return results

def main():
    """
    Entry point for running the sensitivity analysis from the command line.

    Expected arguments:
        --trajectories_dir <path>  : Directory containing trajectory JSONs
        --output <path>            : Output JSON path
        --rho_values <list>        : Comma-separated list of rho values (optional)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis sweep for p-value validity study."
    )
    parser.add_argument(
        "--trajectories_dir",
        type=str,
        required=True,
        help="Path to directory containing trajectory JSON files."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to write the sensitivity analysis results JSON."
    )
    parser.add_argument(
        "--rho_values",
        type=str,
        default="0.0,0.1,0.3,0.5,0.7,0.9",
        help="Comma-separated list of rho values to sweep (default: 0.0,0.1,0.3,0.5,0.7,0.9)"
    )

    args = parser.parse_args()

    # Parse rho values
    try:
        rho_list = [float(x.strip()) for x in args.rho_values.split(",")]
    except ValueError as e:
        logger.error(f"Invalid rho_values format: {e}")
        sys.exit(1)

    trajectories_dir = Path(args.trajectories_dir)
    output_path = Path(args.output)

    if not trajectories_dir.exists():
        logger.error(f"Trajectories directory does not exist: {trajectories_dir}")
        sys.exit(1)

    results = run_sensitivity_analysis(
        trajectories_dir=trajectories_dir,
        output_path=output_path,
        rho_values=rho_list
    )

    # Print summary
    print("\n--- Sensitivity Analysis Summary ---")
    for res in results["sensitivity_results"]:
        if "error" in res:
            print(f"rho={res['rho']}: ERROR - {res['error']}")
        else:
            print(
                f"rho={res['rho']}: KS={res['KS_statistic']:.4f}, "
                f"p={res['p_value']:.4f}"
            )
    print("------------------------------------")

    return 0

if __name__ == "__main__":
    sys.exit(main())