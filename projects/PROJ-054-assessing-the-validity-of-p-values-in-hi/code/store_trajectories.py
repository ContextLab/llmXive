"""
Store full p-value trajectories from hypothesis tests to disk.

This module implements T017: Store full p-value trajectories (all p-values per iteration)
in data/synthetic/trajectories/{seed}.json to support US3 analysis (KS calculation, bootstrap CIs).

The trajectory file contains the complete list of p-values generated in each iteration,
allowing downstream analysis of the distribution of p-values under the null hypothesis.
"""

import json
import logging
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np

# Import from project utilities
from utils.exceptions import SimulationError

logger = logging.getLogger(__name__)


def compute_trajectory_hash(pvalues: List[float]) -> str:
    """
    Compute a SHA-256 hash of the p-value trajectory for verification.

    Args:
        pvalues: List of p-values from a single simulation iteration.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    # Convert to a consistent string representation
    # Use repr to ensure float precision is preserved in the hash
    content = json.dumps(pvalues, sort_keys=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def write_trajectory_file(
    trajectory_dir: Path,
    seed: int,
    pvalues: List[float],
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Write p-value trajectory to a JSON file.

    Args:
        trajectory_dir: Directory where the trajectory file will be written.
        seed: The random seed used for this simulation run.
        pvalues: List of p-values collected during the iteration.
        metadata: Optional dictionary of additional metadata to store.

    Returns:
        Path to the written file.

    Raises:
        SimulationError: If the file cannot be written or directory creation fails.
    """
    # Ensure directory exists
    trajectory_dir.mkdir(parents=True, exist_ok=True)

    # Prepare trajectory data
    trajectory_data: Dict[str, Any] = {
        "seed": seed,
        "pvalues": pvalues,
        "n_pvalues": len(pvalues),
        "sha256": compute_trajectory_hash(pvalues)
    }

    # Add metadata if provided
    if metadata:
        trajectory_data["metadata"] = metadata

    # Construct file path
    file_path = trajectory_dir / f"{seed}.json"

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(trajectory_data, f, indent=2)
        logger.info(f"Wrote trajectory for seed {seed} to {file_path}")
        return file_path
    except (IOError, OSError) as e:
        raise SimulationError(f"Failed to write trajectory file {file_path}: {e}")


def main():
    """
    Main entry point for storing p-value trajectories.

    This function is intended to be called by the integration pipeline (T022)
    after hypothesis tests have been run. It reads the collected p-values
    and writes them to the appropriate trajectory file.

    Usage:
        python code/store_trajectories.py --seed 12345 --pvalues "[0.01, 0.5, ...]"
        or called programmatically from the pipeline.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Store p-value trajectories to disk for US3 analysis."
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=True,
        help="Random seed for the simulation run."
    )
    parser.add_argument(
        "--pvalues",
        type=str,
        required=True,
        help="JSON-encoded list of p-values from the hypothesis tests."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/synthetic/trajectories",
        help="Directory to store trajectory files."
    )
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="Sample size (n) for metadata."
    )
    parser.add_argument(
        "--p",
        type=int,
        default=None,
        help="Number of features (p) for metadata."
    )
    parser.add_argument(
        "--rho",
        type=float,
        default=None,
        help="Correlation threshold (rho) for metadata."
    )
    parser.add_argument(
        "--distribution_type",
        type=str,
        default=None,
        help="Distribution type for metadata."
    )

    args = parser.parse_args()

    # Parse p-values from JSON string
    try:
        pvalues = json.loads(args.pvalues)
        if not isinstance(pvalues, list) or not all(isinstance(x, (int, float)) for x in pvalues):
            raise ValueError("pvalues must be a list of numbers")
    except json.JSONDecodeError as e:
        raise SimulationError(f"Failed to parse pvalues JSON: {e}")

    # Build metadata if provided
    metadata = {}
    if args.n is not None:
        metadata["n"] = args.n
    if args.p is not None:
        metadata["p"] = args.p
    if args.rho is not None:
        metadata["rho"] = args.rho
    if args.distribution_type is not None:
        metadata["distribution_type"] = args.distribution_type

    # Write trajectory
    output_path = Path(args.output_dir)
    try:
        write_trajectory_file(
            trajectory_dir=output_path,
            seed=args.seed,
            pvalues=pvalues,
            metadata=metadata if metadata else None
        )
    except SimulationError as e:
        logger.error(str(e))
        return 1

    return 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    exit(main())
