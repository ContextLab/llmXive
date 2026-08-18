"""
Unified Data Generation and Labeling Script for Synthetic Attention Matrices.

This module implements the generation of synthetic attention matrices with controlled
statistical properties (mean, variance, sparsity, outliers) and computes ground-truth
scaling factors using the SingleStepSinkhornSolver.

Output:
    data/raw/synthetic_attention_matrices.parquet: Dataset containing matrix moments
    and computed scaling factors.
    data/raw/synthetic_attention_matrices.parquet.sha256: Checksum file.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

# Import from project API surface
from data_generation.sinkhorn_solver import SingleStepSinkhornSolver, SinkhornNonConvergenceError
from data_generation.utils import (
    get_project_root,
    apply_epsilon_floor,
    setup_generation_logger,
    log_generation_progress,
    log_solver_success,
    log_solver_failure,
    log_numerical_warning,
    log_skipped_instance,
    save_to_parquet,
    compute_and_store_checksums,
    generate_checksum_for_dataset
)
from config import get_config

# Constants
MATRIX_SIZE = 128
TARGET_COUNT = 10000
EPSILON_FLOOR = 1e-6
MAX_OUTLIER_MAGNITUDE = 5.0
MIN_OUTLIER_MAGNITUDE = 0.5
SPARSITY_TARGET = 0.1  # 10% sparsity

@dataclass
class SyntheticMatrixStats:
    """Container for the statistical properties of a generated matrix."""
    mean: float
    variance: float
    sparsity: float
    outlier_magnitude: float
    scaling_factor: float
    convergence_status: str  # 'success', 'failed', 'skipped'

def generate_static_attention_matrix(
    rng: np.random.Generator,
    target_sparsity: float = SPARSITY_TARGET,
    min_outlier: float = MIN_OUTLIER_MAGNITUDE,
    max_outlier: float = MAX_OUTLIER_MAGNITUDE
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Generates a single synthetic attention matrix with controlled properties.

    The matrix is constructed by:
    1. Sampling base values from a normal distribution.
    2. Applying a sparsity mask.
    3. Injecting outliers to simulate attention spikes.

    Args:
        rng: NumPy random generator for reproducibility.
        target_sparsity: Target fraction of zero elements.
        min_outlier: Minimum magnitude for injected outliers.
        max_outlier: Maximum magnitude for injected outliers.

    Returns:
        Tuple of (matrix, stats_dict).
    """
    # 1. Base generation: Normal distribution centered at 0
    base_matrix = rng.normal(loc=0.0, scale=1.0, size=(MATRIX_SIZE, MATRIX_SIZE))

    # 2. Apply Sparsity
    # Create a mask where True means keep, False means zero
    keep_mask = rng.random((MATRIX_SIZE, MATRIX_SIZE)) > target_sparsity
    matrix = base_matrix * keep_mask

    # 3. Inject Outliers
    # Determine number of outliers (approx 1% of matrix)
    num_outliers = int(0.01 * MATRIX_SIZE * MATRIX_SIZE)
    outlier_indices = rng.choice(MATRIX_SIZE * MATRIX_SIZE, size=num_outliers, replace=False)
    outlier_values = rng.uniform(min_outlier, max_outlier, size=num_outliers)
    # Assign positive or negative sign randomly
    signs = rng.choice([-1, 1], size=num_outliers)
    outlier_values = outlier_values * signs

    # Flatten matrix to set outliers easily, then reshape
    flat_matrix = matrix.flatten()
    flat_matrix[outlier_indices] = outlier_values
    matrix = flat_matrix.reshape((MATRIX_SIZE, MATRIX_SIZE))

    # 4. Compute Moments
    mean_val = float(np.mean(matrix))
    var_val = float(np.var(matrix))
    sparsity_val = float(1.0 - (np.count_nonzero(matrix) / (MATRIX_SIZE * MATRIX_SIZE)))

    # Outlier magnitude: max absolute value (simplified metric for this task)
    outlier_mag = float(np.max(np.abs(matrix)))

    stats = {
        "mean": mean_val,
        "variance": var_val,
        "sparsity": sparsity_val,
        "outlier_magnitude": outlier_mag
    }

    return matrix, stats

def compute_scaling_factor(
    matrix: np.ndarray,
    solver: SingleStepSinkhornSolver,
    logger: logging.Logger
) -> Tuple[Optional[float], str]:
    """
    Computes the ground-truth scaling factor for a given matrix using the Sinkhorn solver.

    Args:
        matrix: The attention matrix.
        solver: The SingleStepSinkhornSolver instance.
        logger: Logger for progress tracking.

    Returns:
        Tuple of (scaling_factor, status).
        scaling_factor is None if convergence failed.
        status is 'success', 'failed', or 'skipped'.
    """
    try:
        # Ensure numerical stability before passing to solver
        # The solver expects a valid matrix, but we apply epsilon floor to variances if needed
        # inside the solver logic. Here we just pass the matrix.
        
        # We need to pass the matrix and an epsilon. 
        # The task requires using SingleStepSinkhornSolver which computes a single factor.
        # The solver signature is solve(matrix, epsilon).
        # We use the global epsilon floor from config or a default.
        config = get_config()
        epsilon = getattr(config, 'EPSILON_FLOOR', EPSILON_FLOOR)
        
        scaling_factor = solver.solve(matrix, epsilon)
        
        if np.isnan(scaling_factor) or np.isinf(scaling_factor):
            log_numerical_warning(logger, f"Solver returned non-finite value: {scaling_factor}")
            return None, "failed"
        
        log_solver_success(logger, scaling_factor)
        return scaling_factor, "success"

    except SinkhornNonConvergenceError as e:
        log_solver_failure(logger, str(e))
        return None, "failed"
    except Exception as e:
        log_numerical_warning(logger, f"Unexpected error in solver: {str(e)}")
        return None, "failed"

def generate_static_dataset(
    num_matrices: int = TARGET_COUNT,
    seed: Optional[int] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Generates the full dataset of synthetic attention matrices and computes labels.

    This function runs the generation loop, computes scaling factors, and writes
    the results to a Parquet file.

    Args:
        num_matrices: Number of matrices to generate (default 10,000).
        seed: Random seed for reproducibility.
        output_dir: Directory to save the output file. Defaults to data/raw.

    Returns:
        Path to the generated Parquet file.
    """
    # Setup
    if seed is None:
        seed = 42 # Default seed
    
    rng = np.random.default_rng(seed)
    solver = SingleStepSinkhornSolver()
    
    project_root = get_project_root()
    if output_dir is None:
        output_dir = project_root / "data" / "raw"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "synthetic_attention_matrices.parquet"
    checksum_file = output_dir / "synthetic_attention_matrices.parquet.sha256"

    # Logger setup
    logger = setup_generation_logger("data_generation")

    logger.info(f"Starting generation of {num_matrices} matrices with seed {seed}")
    logger.info(f"Output will be written to: {output_file}")

    # Data collection lists
    data_rows = []
    success_count = 0
    failure_count = 0

    for i in range(num_matrices):
        # 1. Generate Matrix
        matrix, moments = generate_static_attention_matrix(rng)

        # 2. Compute Scaling Factor
        scaling_factor, status = compute_scaling_factor(matrix, solver, logger)

        if status == "success":
            success_count += 1
            row = {
                "index": i,
                "mean": moments["mean"],
                "variance": moments["variance"],
                "sparsity": moments["sparsity"],
                "outlier_magnitude": moments["outlier_magnitude"],
                "scaling_factor": scaling_factor,
                "status": status
            }
            data_rows.append(row)
        else:
            failure_count += 1
            log_skipped_instance(logger, i, status)
            # We do not store failed instances in the final dataset as per requirement 
            # "do not produce NaN labels". We skip them to ensure the output count is valid.
            # However, to ensure we hit 10,000 VALID entries, we might need to loop more.
            # The task says "generate exactly 10,000 ... matrices ... and write ... containing ... scaling_factor".
            # If we skip failures, we need to generate until we have 10,000 successes.
            # Re-adjusting loop: we need to continue until data_rows has 10,000 items.
            # But the loop is fixed to range(num_matrices). 
            # Let's interpret "generate exactly 10,000" as the target count of the dataset.
            # If the failure rate is low, range(10000) is fine. If high, we need a while loop.
            # Given the robust solver, we assume low failure rate, but to be safe:
            pass

        # Progress logging
        if (i + 1) % 1000 == 0:
            log_generation_progress(logger, i + 1, num_matrices, success_count, failure_count)

    # If we didn't get 10,000 successes, we need to generate more.
    # This ensures the output file has exactly 10,000 valid rows.
    current_count = len(data_rows)
    if current_count < num_matrices:
        logger.warning(f"Only generated {current_count} valid matrices. Generating {num_matrices - current_count} more.")
        needed = num_matrices - current_count
        start_idx = current_count
        while len(data_rows) < num_matrices:
            matrix, moments = generate_static_attention_matrix(rng)
            scaling_factor, status = compute_scaling_factor(matrix, solver, logger)
            if status == "success":
                row = {
                    "index": len(data_rows), # Renumber sequentially
                    "mean": moments["mean"],
                    "variance": moments["variance"],
                    "sparsity": moments["sparsity"],
                    "outlier_magnitude": moments["outlier_magnitude"],
                    "scaling_factor": scaling_factor,
                    "status": status
                }
                data_rows.append(row)
            else:
                failure_count += 1
                log_skipped_instance(logger, len(data_rows) + start_idx, status)
        
        logger.info(f"Completed generation of {num_matrices} valid matrices.")

    # Create DataFrame
    df = pd.DataFrame(data_rows)
    
    # Verify count
    if len(df) != num_matrices:
        raise RuntimeError(f"Dataset generation failed: expected {num_matrices} rows, got {len(df)}")

    # 3. Serialize to Parquet
    save_to_parquet(df, output_file)
    logger.info(f"Successfully wrote dataset to {output_file}")

    # 4. Generate Checksum
    generate_checksum_for_dataset(output_file, checksum_file)
    logger.info(f"Successfully wrote checksum to {checksum_file}")

    logger.info(f"Data generation complete. Total rows: {len(df)}, Successes: {success_count}, Failures: {failure_count}")
    
    return output_file

def main():
    """Entry point for the data generation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic attention matrices dataset.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed. Default: 42")
    parser.add_argument("--count", type=int, default=TARGET_COUNT, help=f"Number of matrices to generate. Default: {TARGET_COUNT}")
    parser.add_argument("--output", type=str, default=None, help="Output file path. Default: data/raw/synthetic_attention_matrices.parquet")
    
    args = parser.parse_args()
    
    output_path = None
    if args.output:
        output_path = Path(args.output)
        
    try:
        generate_static_dataset(num_matrices=args.count, seed=args.seed, output_dir=output_path.parent if output_path else None)
        print("Data generation completed successfully.")
    except Exception as e:
        logging.error(f"Data generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
