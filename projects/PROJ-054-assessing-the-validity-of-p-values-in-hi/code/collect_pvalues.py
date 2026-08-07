"""
P-value collection module for User Story 2.

This module implements the logic to collect exactly p p-values per iteration
from hypothesis tests run on high-dimensional synthetic data, satisfying FR-003.
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from utils.exceptions import HypothesisTestError


def collect_pvalues(
    pvalues: List[float],
    iteration: int,
    n_features: int,
    seed: int,
    output_dir: Path,
    rho: float,
    n_samples: int
) -> Dict[str, Any]:
    """
    Collect and validate p-values ensuring exactly n_features (p) values per iteration.

    This function enforces FR-003: the number of collected p-values must equal
    the dimensionality of the data (p).

    Args:
        pvalues: List of p-values from hypothesis tests (expected length = n_features).
        iteration: Current simulation iteration count.
        n_features: The dimensionality 'p' of the data.
        seed: Random seed used for this dataset generation.
        output_dir: Directory where trajectory files will be stored.
        rho: Correlation parameter used in data generation.
        n_samples: Sample size 'n' used in data generation.

    Returns:
        Dictionary containing the validated p-value collection and metadata.

    Raises:
        HypothesisTestError: If the number of p-values does not match n_features.
    """
    if len(pvalues) != n_features:
        raise HypothesisTestError(
            f"FR-003 Violation: Expected exactly {n_features} p-values for "
            f"dimensionality p, but got {len(pvalues)} values at iteration {iteration}."
        )

    # Ensure all p-values are valid floats in [0, 1]
    for i, pv in enumerate(pvalues):
        if not isinstance(pv, (int, float)) or pv < 0.0 or pv > 1.0:
            raise HypothesisTestError(
                f"Invalid p-value at index {i}: {pv}. Must be a float in [0, 1]."
            )

    # Prepare metadata
    metadata = {
        "iteration": iteration,
        "n_features": n_features,
        "n_samples": n_samples,
        "rho": rho,
        "seed": seed,
        "count": len(pvalues)
    }

    return {
        "metadata": metadata,
        "pvalues": pvalues
    }


def aggregate_pvalues(
    trajectory_data: List[Dict[str, Any]]
) -> np.ndarray:
    """
    Aggregate p-values from multiple iterations into a single flat array.

    Args:
        trajectory_data: List of dictionaries returned by collect_pvalues.

    Returns:
        NumPy array of all collected p-values.
    """
    all_pvalues = []
    for entry in trajectory_data:
        if "pvalues" not in entry:
            raise HypothesisTestError("Invalid trajectory entry: missing 'pvalues' key")
        all_pvalues.extend(entry["pvalues"])

    return np.array(all_pvalues)


def write_trajectory_snapshot(
    data: Dict[str, Any],
    filepath: Path
) -> None:
    """
    Write a single iteration's p-value collection to a JSON file.

    Args:
        data: The dictionary returned by collect_pvalues.
        filepath: Path to the output JSON file.
    """
    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Compute hash of the p-values for integrity verification
    pvalues_str = json.dumps(data["pvalues"], sort_keys=True)
    pvalues_hash = hashlib.sha256(pvalues_str.encode('utf-8')).hexdigest()

    output_record = {
        "iteration": data["metadata"]["iteration"],
        "count": data["metadata"]["count"],
        "pvalues_hash": pvalues_hash,
        "pvalues": data["pvalues"],
        "meta": {
            "n_features": data["metadata"]["n_features"],
            "n_samples": data["metadata"]["n_samples"],
            "rho": data["metadata"]["rho"],
            "seed": data["metadata"]["seed"]
        }
    }

    with open(filepath, 'w') as f:
        json.dump(output_record, f, indent=2)


def main():
    """
    Main entry point for testing the collection logic independently.
    Simulates a single iteration to verify FR-003 enforcement.
    """
    import sys
    import logging

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)

    # Simulate parameters
    n_features = 100  # p
    n_samples = 50    # n
    rho = 0.5
    seed = 42
    iteration = 1

    # Generate synthetic p-values (under null, should be uniform, but we just need valid floats)
    # In real usage, these come from run_hypothesis_tests
    synthetic_pvalues = np.random.uniform(0, 1, n_features).tolist()

    output_dir = Path("data/synthetic/trajectories")
    output_file = output_dir / f"test_{seed}_{iteration}.json"

    try:
        # Collect
        result = collect_pvalues(
            pvalues=synthetic_pvalues,
            iteration=iteration,
            n_features=n_features,
            seed=seed,
            output_dir=output_dir,
            rho=rho,
            n_samples=n_samples
        )

        # Write to disk
        write_trajectory_snapshot(result, output_file)

        logger.info(f"Successfully collected {len(result['pvalues'])} p-values.")
        logger.info(f"Wrote trajectory snapshot to: {output_file}")
        logger.info(f"Validation: Count matches n_features? {len(result['pvalues']) == n_features}")

    except HypothesisTestError as e:
        logger.error(f"FR-003 Violation or Data Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()