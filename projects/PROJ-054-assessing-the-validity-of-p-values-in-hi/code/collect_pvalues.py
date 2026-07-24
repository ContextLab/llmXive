"""
P-value collection logic for User Story 2.

This module ensures that exactly p p-values are collected per iteration,
corresponding to the p features/tests performed on the synthetic dataset.
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from utils.exceptions import HypothesisTestError


def collect_pvalues(
    pvalues: List[float],
    n_features: int,
    iteration: int,
    seed: int,
    output_dir: str,
    rho: float,
    n: int,
    p: int,
    distribution_type: str
) -> Dict[str, Any]:
    """
    Collects and validates p-values, ensuring exactly p values are present.

    This function enforces FR-003: "The system must collect exactly p p-values
    per iteration, corresponding to the p features tested."

    Args:
        pvalues: List of p-values returned by hypothesis tests.
        n_features: Expected number of features (p).
        iteration: Current iteration index.
        seed: Random seed used for this dataset.
        output_dir: Directory to store trajectory data.
        rho: Correlation parameter used for generation.
        n: Sample size used for generation.
        p: Number of features/dimensions used for generation.
        distribution_type: Type of distribution used (e.g., 'normal', 't', 'skew').

    Returns:
        Dictionary containing the collected p-values and metadata.

    Raises:
        HypothesisTestError: If the number of collected p-values does not match p.
    """
    # Validate count (FR-003)
    if len(pvalues) != n_features:
        raise HypothesisTestError(
            f"FR-003 Violation: Expected exactly {n_features} p-values for "
            f"{n_features} features, but collected {len(pvalues)}."
        )

    # Ensure directory exists
    traj_dir = Path(output_dir) / "trajectories"
    traj_dir.mkdir(parents=True, exist_ok=True)

    # Construct record
    record = {
        "iteration": iteration,
        "seed": seed,
        "rho": rho,
        "n": n,
        "p": p,
        "distribution_type": distribution_type,
        "pvalues": pvalues,
        "count": len(pvalues)
    }

    # Calculate hash for integrity (Constitution Principle III)
    # We hash the sorted p-values to ensure order-independence for verification
    # while maintaining the full list for analysis.
    pvalues_str = json.dumps(pvalues, sort_keys=True)
    record_hash = hashlib.sha256(pvalues_str.encode('utf-8')).hexdigest()
    record["sha256_pvalues"] = record_hash

    # Write trajectory file
    filepath = traj_dir / f"{seed}_iter{iteration}.json"
    with open(filepath, 'w') as f:
        json.dump(record, f, indent=2)

    return record

def aggregate_pvalues(
    records: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Aggregates collected p-value records into a single file for analysis.

    Args:
        records: List of dictionaries returned by collect_pvalues.
        output_path: Path to the aggregated output file.
    """
    if not records:
        raise ValueError("No records to aggregate.")

    # Flatten all p-values into a single list for distribution analysis
    all_pvalues = []
    meta = []

    for rec in records:
        all_pvalues.extend(rec["pvalues"])
        # Keep metadata for stratification if needed later
        meta.append({
            "seed": rec["seed"],
            "rho": rec["rho"],
            "n": rec["n"],
            "p": rec["p"],
            "count": rec["count"]
        })

    aggregate_record = {
        "total_pvalues": len(all_pvalues),
        "total_iterations": len(records),
        "pvalues": all_pvalues,
        "metadata": meta
    }

    with open(output_path, 'w') as f:
        json.dump(aggregate_record, f, indent=2)
