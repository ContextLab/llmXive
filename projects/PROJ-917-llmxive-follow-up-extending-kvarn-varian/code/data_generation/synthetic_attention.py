"""
Unified Data Generation and Labeling Script for Synthetic Attention Matrices.

This script generates synthetic static attention matrices with controlled
statistical properties (mean, variance, sparsity, outlier magnitude) and
computes ground-truth scaling factors using the SingleStepSinkhornSolver.

Output:
    data/raw/synthetic_attention_matrices.jsonl: JSONL file containing
    matrix statistics and computed scaling factors.
"""

import os
import sys
import logging
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd

# Local imports based on API surface
from config import Config, get_config
from data_generation.sinkhorn_solver import SingleStepSinkhornSolver, SinkhornNonConvergenceError
from data_generation.utils import (
    get_project_root,
    setup_generation_logger,
    log_generation_progress,
    log_solver_success,
    log_solver_failure,
    log_numerical_warning,
    log_skipped_instance,
    apply_epsilon_floor,
    compute_checksum,
    save_checksum_to_file
)
from entities import AttentionMatrix, ScalingFactor

@dataclass
class SyntheticMatrixStats:
    """Container for the computed statistics of a generated matrix."""
    mean: float
    variance: float
    sparsity: float
    outlier_magnitude: float
    scaling_factor: Optional[float]
    convergence_success: bool
    generation_time_ms: float
    solver_time_ms: float
    seed_used: int

def generate_static_attention_matrix(
    shape: Tuple[int, int],
    target_sparsity: float,
    target_outlier_magnitude: float,
    seed: int,
    epsilon_floor: float
) -> Tuple[np.ndarray, SyntheticMatrixStats]:
    """
    Generate a synthetic static attention matrix with controlled properties.

    Args:
        shape: Dimensions of the matrix (e.g., (128, 128)).
        target_sparsity: Target ratio of zero elements.
        target_outlier_magnitude: Target magnitude for outlier values.
        seed: Random seed for reproducibility.
        epsilon_floor: Minimum value for numerical stability.

    Returns:
        Tuple of (matrix, stats).
    """
    rng = np.random.default_rng(seed)
    start_time = time.perf_counter()

    # 1. Generate base dense matrix from normal distribution
    # Using a moderate scale to ensure variance is meaningful
    base_matrix = rng.normal(loc=0.0, scale=1.0, size=shape)

    # 2. Enforce Sparsity
    # Create a mask for non-zero elements
    non_zero_mask = rng.random(shape) > target_sparsity
    sparse_matrix = base_matrix * non_zero_mask

    # 3. Inject Outliers
    # Determine number of outliers based on a small percentage (e.g., 0.1% to 1%)
    num_outliers = int(shape[0] * shape[1] * 0.001)
    if num_outliers > 0:
        flat_indices = rng.choice(shape[0] * shape[1], size=num_outliers, replace=False)
        for idx in flat_indices:
            r, c = divmod(idx, shape[1])
            # Sign is random, magnitude is fixed target
            sign = rng.choice([-1, 1])
            sparse_matrix[r, c] = sign * target_outlier_magnitude

    # 4. Apply Epsilon Floor to ensure numerical stability for Sinkhorn
    # This prevents log(0) or division by zero in the solver
    stable_matrix = apply_epsilon_floor(sparse_matrix, epsilon_floor)

    end_gen_time = time.perf_counter()
    generation_time_ms = (end_gen_time - start_time) * 1000

    # 5. Calculate Moments
    mean_val = float(np.mean(stable_matrix))
    var_val = float(np.var(stable_matrix))
    # Sparsity is calculated as ratio of zeros (or near-zeros if we consider epsilon)
    # Here we count strictly zero or very close to zero
    sparsity_val = float(np.sum(np.abs(stable_matrix) < epsilon_floor) / stable_matrix.size)
    # Outlier magnitude: max absolute value (since we injected known outliers)
    outlier_val = float(np.max(np.abs(stable_matrix)))

    return stable_matrix, SyntheticMatrixStats(
        mean=mean_val,
        variance=var_val,
        sparsity=sparsity_val,
        outlier_magnitude=outlier_val,
        scaling_factor=None, # To be filled by solver
        convergence_success=False,
        generation_time_ms=generation_time_ms,
        solver_time_ms=0.0,
        seed_used=seed
    )

def compute_scaling_factor(
    matrix: np.ndarray,
    solver: SingleStepSinkhornSolver,
    epsilon: float
) -> Tuple[Optional[float], float]:
    """
    Compute the ground-truth scaling factor using the Sinkhorn solver.

    Args:
        matrix: The attention matrix.
        solver: The SingleStepSinkhornSolver instance.
        epsilon: The epsilon parameter for the solver.

    Returns:
        Tuple of (scaling_factor, solver_time_ms).
    """
    start_time = time.perf_counter()
    try:
        sf = solver.solve(matrix, epsilon)
        end_time = time.perf_counter()
        return sf, (end_time - start_time) * 1000
    except SinkhornNonConvergenceError:
        end_time = time.perf_counter()
        return None, (end_time - start_time) * 1000

def generate_static_dataset(
    num_matrices: int,
    output_path: Path,
    logger: logging.Logger
) -> List[SyntheticMatrixStats]:
    """
    Main generation loop. Generates matrices and computes labels.

    Args:
        num_matrices: Total number of matrices to generate.
        output_path: Path to the output JSONL file.
        logger: Logger instance.

    Returns:
        List of SyntheticMatrixStats for verification (in memory).
    """
    config = get_config()
    solver = SingleStepSinkhornSolver()
    epsilon = config.EPSILON_FLOOR # Using the config epsilon for solver

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    stats_list: List[SyntheticMatrixStats] = []
    successful_count = 0
    skipped_count = 0

    # Open file for writing
    with open(output_path, 'w', encoding='utf-8') as f:
        for i in range(num_matrices):
            # Deterministic seed for each matrix
            seed = config.RANDOM_SEED + i
            matrix, stats = generate_static_attention_matrix(
                shape=(128, 128),
                target_sparsity=0.9, # High sparsity typical for attention
                target_outlier_magnitude=10.0,
                seed=seed,
                epsilon_floor=config.EPSILON_FLOOR
            )

            # Compute scaling factor
            sf, solver_time = compute_scaling_factor(matrix, solver, epsilon)
            stats.solver_time_ms = solver_time

            if sf is not None and not np.isnan(sf) and not np.isinf(sf):
                stats.scaling_factor = sf
                stats.convergence_success = True
                successful_count += 1
            else:
                log_skipped_instance(logger, i, seed, "Sinkhorn non-convergence or NaN")
                stats.convergence_success = False
                skipped_count += 1
                # Do not write this row to the final dataset to avoid NaN labels
                continue

            stats_list.append(stats)

            # Serialize to JSONL
            record = {
                "index": i,
                "seed": seed,
                "shape": [128, 128],
                "mean": stats.mean,
                "variance": stats.variance,
                "sparsity": stats.sparsity,
                "outlier_magnitude": stats.outlier_magnitude,
                "scaling_factor": stats.scaling_factor,
                "convergence_success": stats.convergence_success,
                "generation_time_ms": stats.generation_time_ms,
                "solver_time_ms": stats.solver_time_ms
            }
            f.write(json.dumps(record) + '\n')

            # Log progress
            log_generation_progress(logger, i + 1, num_matrices, successful_count, skipped_count)

    logger.info(f"Generation complete. Total: {num_matrices}, Success: {successful_count}, Skipped: {skipped_count}")
    return stats_list

def main():
    """
    Main entry point for the synthetic attention data generation script.
    """
    project_root = get_project_root()
    logger = setup_generation_logger("synthetic_attention")
    logger.info("Starting Unified Data Generation and Labeling (T017c)...")

    config = get_config()
    num_matrices = config.NUM_MATRICES
    output_file = project_root / "data" / "raw" / "synthetic_attention_matrices.jsonl"

    logger.info(f"Configuration: NUM_MATRICES={num_matrices}, SEED={config.RANDOM_SEED}")

    try:
        stats = generate_static_dataset(num_matrices, output_file, logger)
        logger.info(f"Successfully generated {len(stats)} valid records.")

        # Generate and save checksum
        checksum = compute_checksum(output_file)
        logger.info(f"Checksum computed: {checksum}")
        save_checksum_to_file(output_file, checksum)
        logger.info(f"Checksum saved to {output_file}.sha256")

        logger.info("Task T017c completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Critical failure in data generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())