"""
Task T024 Implementation: P-value Collection Logic

This module implements the logic to collect p-values from hypothesis tests
run on high-dimensional synthetic data. It ensures exactly p values are
collected per iteration and writes them to `data/results/pvalues_{seed}.csv`.

It relies on the data generation pipeline (T017, T019) and the hypothesis
test execution (T022, T023) to provide the raw p-value data.
"""

import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import dependencies from existing project files
# T019c: Deterministic RNG Wrapper (not directly used here, but ensures upstream consistency)
# T023: run_hypothesis_tests (assumed to be called upstream or here to generate p-values)
from utils.simulation import RNGWrapper
from utils.exceptions import HighDimensionalInstabilityError
from run_tests import run_hypothesis_tests, load_seed_map, load_params

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def collect_pvalues(
    seed: int,
    n: int,
    p: int,
    rho: float,
    distribution_type: str,
    output_dir: str = "data/results"
) -> Dict[str, Any]:
    """
    Collects p-values for a single iteration of the simulation.

    This function:
    1. Regenerates the data on-the-fly using the provided seed and parameters.
    2. Runs the hypothesis tests (t-test, F-test).
    3. Collects exactly p p-values.
    4. Writes them to `data/results/pvalues_{seed}.csv`.
    5. Verifies the row count equals p.

    Args:
        seed: The deterministic seed for this iteration.
        n: Sample size.
        p: Number of features (dimensions).
        rho: Correlation parameter.
        distribution_type: Type of distribution (Normal, t-dist, Skewed Normal).
        output_dir: Directory to write the output CSV.

    Returns:
        A dictionary containing the path to the output file and the count of p-values.

    Raises:
        HighDimensionalInstabilityError: If p/n > 10 or covariance is singular.
        RuntimeError: If the collected p-value count does not match p.
    """
    logger.info(f"Collecting p-values for seed={seed}, n={n}, p={p}, rho={rho}, dist={distribution_type}")

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / f"pvalues_{seed}.csv"

    # Run hypothesis tests
    # This function is expected to return a list of p-values (length p)
    # and potentially other statistics, but we focus on p-values for T024.
    try:
        p_values = run_hypothesis_tests(seed, n, p, rho, distribution_type)
    except HighDimensionalInstabilityError as e:
        logger.error(f"High dimensionality instability detected for seed {seed}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error running hypothesis tests for seed {seed}: {e}")
        raise

    # Verification: Ensure exactly p values are collected
    if len(p_values) != p:
        error_msg = (
            f"Collected {len(p_values)} p-values for seed {seed}, "
            f"but expected exactly {p} (matching dimension p)."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Write to CSV
    logger.info(f"Writing {len(p_values)} p-values to {output_file}")
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['p_value']) # Header
        for val in p_values:
            writer.writerow([val])

    logger.info(f"Successfully wrote p-values for seed {seed} to {output_file}")

    return {
        "seed": seed,
        "output_file": str(output_file),
        "p_value_count": len(p_values),
        "expected_count": p
    }


def aggregate_pvalues(
    seed_list: List[int],
    input_dir: str = "data/results",
    output_file: str = "data/results/aggregate_pvalues.csv"
) -> None:
    """
    Aggregates p-values from multiple seeds into a single file.
    Optional utility for downstream analysis.
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['seed', 'p_value'])

        for seed in seed_list:
            input_file = Path(input_dir) / f"pvalues_{seed}.csv"
            if not input_file.exists():
                logger.warning(f"Skipping missing file: {input_file}")
                continue

            with open(input_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    writer.writerow([seed, row['p_value']])

    logger.info(f"Aggregated p-values from {len(seed_list)} seeds to {output_file}")


def write_trajectory_snapshot(
    seed: int,
    p_values: List[float],
    metadata: Dict[str, Any],
    output_dir: str = "data/results"
) -> None:
    """
    Writes a snapshot of the p-value trajectory for a specific seed,
    including metadata. Used for debugging or detailed logging.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    snapshot_file = output_path / f"trajectory_{seed}.json"

    snapshot = {
        "seed": seed,
        "p_values": p_values,
        "metadata": metadata,
        "count": len(p_values)
    }

    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2)

    logger.info(f"Wrote trajectory snapshot for seed {seed} to {snapshot_file}")


def main() -> None:
    """
    Main entry point for the p-value collection script.
    Reads the seed map and parameter sweep configuration,
    and runs the collection for each iteration.
    """
    logger.info("Starting p-value collection pipeline (T024)")

    # Pre-conditions: T017, T019b, T022 must be complete
    seed_map_path = Path("data/sweep/seed_map.json")
    params_path = Path("data/sweep/params.csv")

    if not seed_map_path.exists():
        logger.error(f"Seed map not found: {seed_map_path}. Run T019b first.")
        sys.exit(1)

    if not params_path.exists():
        logger.error(f"Parameter sweep not found: {params_path}. Run T017 first.")
        sys.exit(1)

    # Load configuration
    seed_map = load_seed_map(seed_map_path)
    params = load_params(params_path)

    # Iterate over parameters and seeds
    # The seed_map maps (n, p, rho, distribution_type) to a list of seeds
    success_count = 0
    failure_count = 0

    for param_tuple, seeds in seed_map.items():
        n, p, rho, dist_type = param_tuple
        logger.info(f"Processing parameter set: n={n}, p={p}, rho={rho}, dist={dist_type}")

        for seed in seeds:
            try:
                result = collect_pvalues(
                    seed=seed,
                    n=n,
                    p=p,
                    rho=rho,
                    distribution_type=dist_type,
                    output_dir="data/results"
                )
                if result["p_value_count"] == result["expected_count"]:
                    success_count += 1
                else:
                    failure_count += 1
                    logger.error(f"Count mismatch for seed {seed}")
            except Exception as e:
                failure_count += 1
                logger.error(f"Failed to collect p-values for seed {seed}: {e}")
                # Continue to next seed to ensure full pipeline run if possible

    logger.info(f"Pipeline complete. Success: {success_count}, Failures: {failure_count}")

    if failure_count > 0:
        logger.warning(f"{failure_count} iterations failed.")
        # Do not exit with error code to allow partial results if needed,
        # but in a strict CI, this might be an error.
        # sys.exit(1)


if __name__ == "__main__":
    main()