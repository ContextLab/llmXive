"""
Trajectory analysis utilities for migration route shift permutation tests.

This module implements permutation testing for trajectory shift magnitudes
to generate null distributions and compute p-values for statistical significance.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from joblib import Parallel, delayed

from src.lib.config import setup_logging
from src.models.trajectory import compute_trajectory_shift, load_centroid_data

# Configure logging
logger = logging.getLogger(__name__)
setup_logging()

# Constants
DEFAULT_N_SHUFFLES = 10000
INTERIM_CHECKPOINT = 100
EARLY_STOP_THRESHOLD = 0.001


def _shuffle_trajectory_labels(centroids: Dict[str, Any]) -> Dict[str, Any]:
    """
    Shuffle the year labels within each species to break temporal correlation.

    Args:
        centroids: Dictionary mapping species -> year -> centroid data

    Returns:
        Shuffled copy of centroids with years permuted within each species
    """
    shuffled = {}
    for species, year_data in centroids.items():
        years = list(year_data.keys())
        if len(years) <= 1:
            shuffled[species] = year_data.copy()
            continue

        # Permute years within this species
        permuted_years = np.random.permutation(years)
        shuffled[species] = {
            old_year: year_data[new_year]
            for old_year, new_year in zip(years, permuted_years)
        }
    return shuffled


def _compute_shift_for_permutation(centroids: Dict[str, Any], species: str) -> float:
    """
    Compute trajectory shift magnitude for a single species with permuted labels.

    Args:
        centroids: Dictionary of centroid data
        species: Species name to compute shift for

    Returns:
        Shift magnitude for this species
    """
    try:
        species_centroids = centroids.get(species)
        if species_centroids is None or len(species_centroids) < 2:
            return 0.0

        # Compute shift with shuffled labels
        shift_result = compute_trajectory_shift(species_centroids)
        return shift_result.get('shift_magnitude', 0.0)
    except Exception as e:
        logger.warning(f"Error computing shift for {species}: {e}")
        return 0.0


def run_trajectory_permutation_test(
    centroids_file: str,
    output_file: str,
    n_shuffles: int = DEFAULT_N_SHUFFLES,
    n_jobs: int = 1,
    batch_size: int = 100,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run permutation test for trajectory shift magnitudes.

    This function performs a permutation test to generate a null distribution
    of shift magnitudes by randomly shuffling year labels within each species.
    It implements early stopping checks at interim checkpoints but always
    completes the full number of shuffles.

    Args:
        centroids_file: Path to JSON file containing centroid data
        output_file: Path to write permutation results JSON
        n_shuffles: Total number of permutations to run (default: 10000)
        n_jobs: Number of parallel jobs (default: 1 for CI compatibility)
        batch_size: Batch size for joblib parallelization
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing permutation test results
    """
    if seed is not None:
        np.random.seed(seed)

    logger.info(f"Starting trajectory permutation test with {n_shuffles} shuffles")
    start_time = time.time()

    # Load centroid data
    centroids = load_centroid_data(centroids_file)
    if not centroids:
        logger.error("No centroid data loaded")
        raise ValueError(f"No centroid data found in {centroids_file}")

    species_list = list(centroids.keys())
    logger.info(f"Found {len(species_list)} species for permutation test")

    # Compute observed shifts for all species
    observed_shifts = {}
    for species in species_list:
        shift = _compute_shift_for_permutation(centroids, species)
        observed_shifts[species] = shift

    logger.info(f"Computed observed shifts for {len(observed_shifts)} species")

    # Storage for null distribution
    null_distributions = {species: [] for species in species_list}
    early_stop_flags = {species: False for species in species_list}

    # Run permutation test
    shuffle_count = 0
    interim_results = []

    for shuffle_idx in range(n_shuffles):
        # Shuffle labels
        shuffled_centroids = _shuffle_trajectory_labels(centroids)

        # Compute shifts for all species in parallel
        if n_jobs > 1:
            shifts = Parallel(n_jobs=n_jobs, batch_size=batch_size)(
                delayed(_compute_shift_for_permutation)(shuffled_centroids, species)
                for species in species_list
            )
        else:
            shifts = [
                _compute_shift_for_permutation(shuffled_centroids, species)
                for species in species_list
            ]

        # Store null distribution values
        for i, species in enumerate(species_list):
            null_distributions[species].append(shifts[i])

        shuffle_count += 1

        # Check interim results
        if shuffle_count % INTERIM_CHECKPOINT == 0:
            interim_p_values = {}
            for species in species_list:
                observed = observed_shifts[species]
                null_vals = null_distributions[species]
                if len(null_vals) > 0:
                    # Two-sided p-value
                    extreme_count = sum(1 for v in null_vals if abs(v) >= abs(observed))
                    p_val = (extreme_count + 1) / (len(null_vals) + 1)
                    interim_p_values[species] = p_val

                    # Check early stopping condition
                    if p_val < EARLY_STOP_THRESHOLD:
                        early_stop_flags[species] = True

            logger.info(
                f"Shuffle {shuffle_count}/{n_shuffles}: "
                f"Early stop flags: {sum(early_stop_flags.values())}/{len(species_list)}"
            )

            # Save interim results
            interim_results.append({
                'shuffle_count': shuffle_count,
                'p_values': interim_p_values,
                'early_stop_flags': early_stop_flags.copy()
            })

    # Compute final p-values
    final_results = []
    for species in species_list:
        observed = observed_shifts[species]
        null_vals = null_distributions[species]

        if len(null_vals) == 0:
            p_value = 1.0
        else:
            # Two-sided p-value: proportion of null values as or more extreme than observed
            extreme_count = sum(1 for v in null_vals if abs(v) >= abs(observed))
            p_value = (extreme_count + 1) / (len(null_vals) + 1)

        final_results.append({
            'species': species,
            'shift_magnitude': float(observed),
            'p_value': float(p_value),
            'n_shuffles': n_shuffles,
            'early_stop_flag': early_stop_flags[species],
            'final_p_value': float(p_value)
        })

    # Prepare output
    output_data = {
        'n_shuffles': n_shuffles,
        'total_time_seconds': time.time() - start_time,
        'early_stop_summary': {
            'species_with_early_stop': sum(1 for v in early_stop_flags.values() if v),
            'total_species': len(species_list)
        },
        'results': final_results,
        'interim_checkpoints': len(interim_results)
    }

    # Write results to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(
        f"Permutation test completed in {time.time() - start_time:.2f}s. "
        f"Results written to {output_file}"
    )

    return output_data


def main():
    """Main entry point for trajectory permutation test."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run permutation test for trajectory shift magnitudes'
    )
    parser.add_argument(
        '--centroids-file',
        type=str,
        default='data/processed/trajectory_centroids.json',
        help='Path to centroid data JSON file'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default='data/processed/trajectory_permutation_results.json',
        help='Path to output results JSON file'
    )
    parser.add_argument(
        '--n-shuffles',
        type=int,
        default=DEFAULT_N_SHUFFLES,
        help='Number of permutation shuffles (default: 10000)'
    )
    parser.add_argument(
        '--n-jobs',
        type=int,
        default=1,
        help='Number of parallel jobs (default: 1)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for joblib (default: 100)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )

    args = parser.parse_args()

    result = run_trajectory_permutation_test(
        centroids_file=args.centroids_file,
        output_file=args.output_file,
        n_shuffles=args.n_shuffles,
        n_jobs=args.n_jobs,
        batch_size=args.batch_size,
        seed=args.seed
    )

    print(f"Permutation test completed. Results saved to {args.output_file}")
    print(f"Total shuffles: {result['n_shuffles']}")
    print(f"Time elapsed: {result['total_time_seconds']:.2f}s")


if __name__ == '__main__':
    main()
