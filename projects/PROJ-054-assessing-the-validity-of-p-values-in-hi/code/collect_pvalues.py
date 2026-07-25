"""
P-value collection module for high-dimensional hypothesis testing.

This module implements the logic to collect p-values from hypothesis tests
ensuring exactly p values are gathered per iteration as required by FR-003.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from utils.exceptions import HypothesisTestError


def collect_pvalues(
    pvalue_matrix: np.ndarray,
    iteration_seed: int,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Collect and validate p-values from hypothesis test results.

    Ensures exactly p values are collected per iteration, validating against
    the expected dimension count.

    Parameters
    ----------
    pvalue_matrix : np.ndarray
        2D array of shape (iterations, p) containing p-values from hypothesis tests.
        Each row represents one iteration, each column one feature/test.
    iteration_seed : int
        Random seed used for this iteration (for metadata tracking).
    output_dir : Path
        Directory where trajectory files will be stored.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - 'count': number of p-values collected
        - 'expected_count': expected count (p dimension)
        - 'valid': boolean indicating if collection was valid
        - 'file_path': path to stored trajectory file (if written)
        - 'sha256': SHA256 hash of the stored data

    Raises
    ------
    HypothesisTestError
        If the number of collected p-values does not match expected count p.
    """
    if pvalue_matrix.ndim != 2:
        raise HypothesisTestError(
            f"Expected 2D p-value matrix, got {pvalue_matrix.ndim}D"
        )

    n_iterations, p_count = pvalue_matrix.shape

    # Validate exactly p values per iteration
    for i in range(n_iterations):
        row_count = len(pvalue_matrix[i])
        if row_count != p_count:
            raise HypothesisTestError(
                f"Iteration {i}: Expected {p_count} p-values, got {row_count}"
            )

    # Prepare trajectory data structure
    trajectory_data = {
        'seed': iteration_seed,
        'n_iterations': int(n_iterations),
        'p_dimension': int(p_count),
        'pvalues': pvalue_matrix.tolist()
    }

    # Validate we have exactly p values per iteration
    actual_count = len(trajectory_data['pvalues'][0])
    if actual_count != p_count:
        raise HypothesisTestError(
            f"Validation failed: Expected {p_count} p-values per iteration, "
            f"got {actual_count}"
        )

    # Create output directory if needed
    trajectories_dir = output_dir / "trajectories"
    trajectories_dir.mkdir(parents=True, exist_ok=True)

    # Write trajectory file
    output_file = trajectories_dir / f"{iteration_seed}.json"
    with open(output_file, 'w') as f:
        json.dump(trajectory_data, f, indent=2)

    # Compute SHA256 hash for verification
    file_hash = hashlib.sha256(output_file.read_bytes()).hexdigest()

    return {
        'count': actual_count,
        'expected_count': p_count,
        'valid': actual_count == p_count,
        'file_path': str(output_file),
        'sha256': file_hash
    }


def aggregate_pvalues(
    trajectory_files: List[Path]
) -> Dict[str, Any]:
    """
    Aggregate p-values from multiple trajectory files for analysis.

    Parameters
    ----------
    trajectory_files : List[Path]
        List of paths to trajectory JSON files.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - 'all_pvalues': flattened list of all p-values
        - 'total_count': total number of p-values
        - 'sources': list of source file paths
        - 'metadata': list of metadata from each file
    """
    all_pvalues = []
    metadata_list = []

    for file_path in trajectory_files:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Extract all p-values from this trajectory
        pvalues = data.get('pvalues', [])
        for iteration_pvalues in pvalues:
            all_pvalues.extend(iteration_pvalues)

        metadata_list.append({
            'seed': data.get('seed'),
            'n_iterations': data.get('n_iterations'),
            'p_dimension': data.get('p_dimension'),
            'file': str(file_path)
        })

    return {
        'all_pvalues': all_pvalues,
        'total_count': len(all_pvalues),
        'sources': [str(f) for f in trajectory_files],
        'metadata': metadata_list
    }