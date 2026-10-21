"""
Unified Data Generation and Labeling Script.

This script generates synthetic static attention matrices with controlled properties
(mean, variance, sparsity, outlier magnitude) and computes ground‑truth scaling factors
using the SingleStepSinkhornSolver.

Output:
    data/raw/synthetic_attention_matrices.jsonl: A JSONL file containing one record per matrix.
    Each record includes matrix moments, the computed scaling factor, and metadata.
    A SHA‑256 checksum is computed and logged.
"""
import os
import sys
import logging
import json
import hashlib
import time
import random
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List

import numpy as np

# Import project modules using the provided API surface
from config import get_config
from data_generation.sinkhorn_solver import SingleStepSinkhornSolver, SinkhornNonConvergenceError
from data_generation.utils import (
    get_project_root,
    setup_generation_logger,
    log_generation_progress,
    log_solver_success,
    log_solver_failure,
    log_skipped_instance,
    apply_epsilon_floor,
    compute_checksum,
    save_checksum_to_file,
)
from utils.seed_manager import set_seed

@dataclass
class SyntheticMatrixStats:
    """
    Data class to hold the statistics of a generated synthetic attention matrix.
    """
    matrix_id: int
    mean: float
    variance: float
    sparsity: float
    outlier_magnitude: float
    scaling_factor: Optional[float]
    solver_converged: bool
    generation_time_ms: float
    solver_time_ms: float
    seed_used: int

def generate_static_attention_matrix(
    matrix_size: int = 128,
    target_sparsity: float = 0.1,
    target_outlier_magnitude: float = 1.0,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Generate a synthetic static attention matrix with controlled sparsity and outlier magnitudes.

    The matrix is generated as follows:
    1. Start with a random matrix from a standard normal distribution.
    2. Apply an epsilon floor to ensure numerical stability.
    3. Zero out a fraction of elements to achieve the target sparsity.
    4. Inject outliers to achieve the target outlier magnitude.
    5. Apply a final epsilon floor pass.

    Args:
        matrix_size: Size of the square matrix (N x N).
        target_sparsity: Target fraction of zero elements.
        target_outlier_magnitude: Target magnitude for injected outliers.
        seed: Random seed for reproducibility.

    Returns:
        A NumPy array of shape (matrix_size, matrix_size).
    """
    if seed is not None:
        np.random.seed(seed)

    # 1. Base random matrix
    matrix = np.random.randn(matrix_size, matrix_size).astype(np.float32)

    # 2. Apply epsilon floor to the base matrix to ensure stability
    matrix = apply_epsilon_floor(matrix)

    # 3. Sparsity: Zero out a fraction of elements using a Bernoulli mask
    num_zeros = int(matrix_size * matrix_size * target_sparsity)
    zero_indices = np.random.choice(matrix_size * matrix_size, num_zeros, replace=False)
    matrix.flat[zero_indices] = 0.0

    # 4. Outliers: Inject outliers (1 % of elements) with the desired magnitude
    num_outliers = max(1, int(matrix_size * matrix_size * 0.01))
    non_zero_indices = np.where(matrix != 0)[0]
    if len(non_zero_indices) > 0:
        outlier_indices = np.random.choice(
            non_zero_indices, min(num_outliers, len(non_zero_indices)), replace=False
        )
        signs = np.random.choice([-1, 1], size=outlier_indices.shape)
        # Replace selected entries with values centred around the target magnitude
        matrix.flat[outlier_indices] = signs * (target_outlier_magnitude * 0.5 + np.abs(matrix.flat[outlier_indices]) * 0.5)

    # 5. Final epsilon floor pass
    matrix = apply_epsilon_floor(matrix)

    return matrix

def compute_scaling_factor(
    matrix: np.ndarray,
    solver: SingleStepSinkhornSolver,
    epsilon: float,
) -> tuple[float, bool, float]:
    """
    Compute the ground‑truth scaling factor for a given matrix using the Sinkhorn solver.

    Returns:
        (scaling_factor, converged, solver_time_ms)
    """
    start_time = time.perf_counter()
    try:
        scaling_factor = solver.solve(matrix, epsilon)
        converged = True
    except SinkhornNonConvergenceError:
        scaling_factor = float("nan")
        converged = False
    except Exception as e:
        logging.warning(f"Unexpected error in solver: {e}")
        scaling_factor = float("nan")
        converged = False
    finally:
        solver_time_ms = (time.perf_counter() - start_time) * 1000.0

    return scaling_factor, converged, solver_time_ms

def generate_static_dataset(
    num_matrices: int = 10000,
    matrix_size: int = 128,
    target_sparsity: float = 0.1,
    target_outlier_magnitude: float = 1.0,
    epsilon: float = 1e-4,
    output_path: Optional[Path] = None,
    base_seed: Optional[int] = None,
) -> List[SyntheticMatrixStats]:
    """
    Generate a dataset of synthetic attention matrices and compute their scaling factors.

    The function respects the global configuration (`config.NUM_MATRICES`) unless an
    explicit `num_matrices` argument is provided.

    Returns:
        List of SyntheticMatrixStats objects.
    """
    config = get_config()
    # Use the configured number of matrices unless the caller explicitly overrides it
    if num_matrices == 10000 and hasattr(config, "NUM_MATRICES"):
        num_matrices = config.NUM_MATRICES

    if base_seed is None:
        base_seed = config.RANDOM_SEED

    set_seed(base_seed)
    logger = setup_generation_logger()
    logger.info(
        f"Starting dataset generation: {num_matrices} matrices, size {matrix_size}x{matrix_size}"
    )
    logger.info(f"Target sparsity: {target_sparsity}, Outlier magnitude: {target_outlier_magnitude}")
    logger.info(f"Epsilon (solver): {epsilon}, Base seed: {base_seed}")

    solver = SingleStepSinkhornSolver()
    stats_list: List[SyntheticMatrixStats] = []
    successful_count = 0
    failed_count = 0

    # Ensure output directory exists early so that any early failures still leave a clear path
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    start_gen_time = time.perf_counter()

    for i in range(num_matrices):
        current_seed = base_seed + i
        set_seed(current_seed)  # reproducibility per matrix

        # ---- Matrix generation ----
        gen_start = time.perf_counter()
        matrix = generate_static_attention_matrix(
            matrix_size=matrix_size,
            target_sparsity=target_sparsity,
            target_outlier_magnitude=target_outlier_magnitude,
            seed=current_seed,
        )
        gen_time_ms = (time.perf_counter() - gen_start) * 1000.0

        # ---- Moment computation ----
        mean_val = float(np.mean(matrix))
        var_val = float(np.var(matrix))
        sparsity_val = float(np.sum(matrix == 0) / (matrix_size * matrix_size))
        outlier_val = float(np.max(np.abs(matrix)))

        # ---- Solver ----
        scaling_factor, converged, solver_time_ms = compute_scaling_factor(matrix, solver, epsilon)

        # Record stats
        stats = SyntheticMatrixStats(
            matrix_id=i,
            mean=mean_val,
            variance=var_val,
            sparsity=sparsity_val,
            outlier_magnitude=outlier_val,
            scaling_factor=scaling_factor if converged else None,
            solver_converged=converged,
            generation_time_ms=gen_time_ms,
            solver_time_ms=solver_time_ms,
            seed_used=current_seed,
        )
        stats_list.append(stats)

        if converged:
            successful_count += 1
            log_solver_success(logger, i, scaling_factor)
        else:
            failed_count += 1
            log_solver_failure(logger, i, "Non‑convergence")

        # Simple progress logging every 1000 matrices (or at the end)
        if (i + 1) % 1000 == 0 or (i + 1) == num_matrices:
            logger.info(
                f"Progress: {i + 1}/{num_matrices} matrices generated – "
                f"Successful: {successful_count}, Failed: {failed_count}"
            )

    total_time_s = time.perf_counter() - start_gen_time
    logger.info(f"Generation complete. Total elapsed time: {total_time_s:.2f}s")
    logger.info(f"Successful: {successful_count}, Failed/Skipped: {failed_count}")

    # ---- Write JSONL output ----
    if output_path:
        with open(output_path, "w") as f:
            for stats in stats_list:
                record = asdict(stats)
                # Rename 'variance' to 'var' to match downstream expectations
                record["var"] = record.pop("variance")
                # Ensure JSON serialisable None stays as null
                json.dump(record, f)
                f.write("\n")

        # Compute and store SHA‑256 checksum
        checksum = compute_checksum(output_path)
        logger.info(f"Output file written to {output_path}")
        logger.info(f"SHA‑256 Checksum: {checksum}")
        save_checksum_to_file(output_path.with_suffix(".sha256"), checksum)

    return stats_list

def main():
    """
    Main entry point for the synthetic attention data generation script.
    """
    config = get_config()
    output_path = get_project_root() / "data" / "raw" / "synthetic_attention_matrices.jsonl"

    # Run generation using values from the global config
    stats = generate_static_dataset(
        num_matrices=config.NUM_MATRICES,
        matrix_size=128,
        target_sparsity=0.1,
        target_outlier_magnitude=1.0,
        epsilon=config.EPSILON_SWEEP_VALUES[0] if config.EPSILON_SWEEP_VALUES else 1e-4,
        output_path=output_path,
        base_seed=config.RANDOM_SEED,
    )

    # ---- Verification checks ----
    if len(stats) != config.NUM_MATRICES:
        raise RuntimeError(
            f"Generated {len(stats)} matrices, expected {config.NUM_MATRICES}"
        )
    if not output_path.exists():
        raise RuntimeError(f"Output file {output_path} was not created")

    logging.info(f"Task T017c completed successfully. Output: {output_path}")

if __name__ == "__main__":
    main()
