import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_config
from data_generation.sinkhorn_solver import SingleStepSinkhornSolver, SinkhornNonConvergenceError
from data_generation.utils import (
    get_project_root, setup_generation_logger, log_generation_progress,
    log_solver_success, log_solver_failure, log_skipped_instance,
    compute_and_store_checksums
)
from entities import AttentionMatrix, ScalingFactor

logger = setup_generation_logger("synthetic_attention")

class SyntheticMatrixStats:
    """Container for statistical properties of a generated matrix."""
    def __init__(self, mean: float, variance: float, sparsity: float, outlier_magnitude: float):
        self.mean = mean
        self.variance = variance
        self.sparsity = sparsity
        self.outlier_magnitude = outlier_magnitude

def generate_static_attention_matrix(
    shape: Tuple[int, int] = (128, 128),
    target_sparsity: float = 0.1,
    outlier_fraction: float = 0.05,
    outlier_magnitude_factor: float = 10.0,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, SyntheticMatrixStats]:
    """
    Generate a synthetic static attention matrix with controlled properties.
    
    Args:
        shape: Dimensions of the matrix.
        target_sparsity: Target ratio of zero elements.
        outlier_fraction: Fraction of elements to be outliers.
        outlier_magnitude_factor: Multiplier for outlier values relative to std dev.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (matrix, stats)
    """
    if seed is not None:
        np.random.seed(seed)

    n_elements = shape[0] * shape[1]
    
    # Generate base Gaussian values
    base_values = np.random.randn(*shape)
    
    # Apply sparsity (set some values to zero)
    num_zeros = int(n_elements * target_sparsity)
    zero_indices = np.random.choice(n_elements, num_zeros, replace=False)
    base_values.flat[zero_indices] = 0.0
    
    # Calculate current statistics
    current_mean = np.mean(base_values)
    current_std = np.std(base_values)
    
    # Inject outliers
    num_outliers = int(n_elements * outlier_fraction)
    outlier_indices = np.random.choice(n_elements, num_outliers, replace=False)
    # Outliers are set to mean +/- (std * factor)
    outlier_signs = np.random.choice([-1, 1], num_outliers)
    outlier_values = current_mean + outlier_signs * current_std * outlier_magnitude_factor
    base_values.flat[outlier_indices] = outlier_values
    
    # Compute final statistics
    final_mean = np.mean(base_values)
    final_var = np.var(base_values)
    final_sparsity = np.sum(base_values == 0) / n_elements
    # Outlier magnitude is defined as the average absolute deviation of outliers from mean
    outlier_abs_devs = np.abs(base_values.flat[outlier_indices] - final_mean)
    final_outlier_mag = np.mean(outlier_abs_devs) if num_outliers > 0 else 0.0
    
    stats = SyntheticMatrixStats(
        mean=final_mean,
        variance=final_var,
        sparsity=final_sparsity,
        outlier_magnitude=final_outlier_mag
    )
    
    return base_values, stats

def compute_scaling_factor(
    matrix: np.ndarray,
    solver: SingleStepSinkhornSolver,
    epsilon: Optional[float] = None
) -> float:
    """
    Compute the ground-truth scaling factor for a matrix using the Sinkhorn solver.
    
    Args:
        matrix: The attention matrix.
        solver: The solver instance.
        epsilon: Epsilon parameter for the solver (optional).
        
    Returns:
        The computed scaling factor.
        
    Raises:
        SinkhornNonConvergenceError: If the solver fails to converge.
    """
    try:
        # The solver expects a matrix and epsilon
        if epsilon is not None:
            return solver.solve(matrix, epsilon)
        else:
            config = get_config()
            default_epsilon = getattr(config, 'EPSILON_FLOOR', 1e-6)
            return solver.solve(matrix, default_epsilon)
    except SinkhornNonConvergenceError as e:
        raise e

def generate_static_dataset(
    num_matrices: int,
    matrix_shape: Tuple[int, int] = (128, 128),
    target_sparsity: float = 0.1,
    outlier_fraction: float = 0.05,
    outlier_magnitude_factor: float = 10.0,
    output_path: Optional[Path] = None,
    seed_base: int = 42
) -> pd.DataFrame:
    """
    Generate a dataset of synthetic attention matrices and their ground-truth scaling factors.
    
    Args:
        num_matrices: Number of matrices to generate.
        matrix_shape: Shape of each matrix.
        target_sparsity: Target sparsity ratio.
        outlier_fraction: Fraction of outliers.
        outlier_magnitude_factor: Outlier magnitude multiplier.
        output_path: Path to save the CSV output.
        seed_base: Base seed for generation.
        
    Returns:
        DataFrame containing the generated data.
    """
    config = get_config()
    solver = SingleStepSinkhornSolver()
    epsilon = getattr(config, 'EPSILON_FLOOR', 1e-6)
    
    data_rows = []
    skipped_count = 0
    
    logger.info(f"Starting generation of {num_matrices} matrices...")
    
    for i in range(num_matrices):
        current_seed = seed_base + i
        try:
            # Generate matrix
            matrix, stats = generate_static_attention_matrix(
                shape=matrix_shape,
                target_sparsity=target_sparsity,
                outlier_fraction=outlier_fraction,
                outlier_magnitude_factor=outlier_magnitude_factor,
                seed=current_seed
            )
            
            # Compute scaling factor
            try:
                scaling_factor = compute_scaling_factor(matrix, solver, epsilon)
                
                # Check for numerical stability
                if not np.isfinite(scaling_factor):
                    log_skipped_instance(logger, i, "Non-finite scaling factor")
                    skipped_count += 1
                    continue
                    
                row = {
                    'index': i,
                    'mean': stats.mean,
                    'variance': stats.variance,
                    'sparsity': stats.sparsity,
                    'outlier_magnitude': stats.outlier_magnitude,
                    'scaling_factor': scaling_factor
                }
                data_rows.append(row)
                log_solver_success(logger, i, scaling_factor)
                
            except SinkhornNonConvergenceError:
                log_skipped_instance(logger, i, "Sinkhorn solver did not converge")
                skipped_count += 1
                continue
                
        except Exception as e:
            log_skipped_instance(logger, i, f"Unexpected error: {str(e)}")
            skipped_count += 1
            continue
            
        log_generation_progress(logger, i + 1, num_matrices)
        
    df = pd.DataFrame(data_rows)
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved dataset to {output_path}")
        
        # Generate checksum
        try:
            checksum_path = compute_and_store_checksums(output_path)
            logger.info(f"Saved checksum to {checksum_path}")
        except Exception as e:
            logger.error(f"Failed to generate checksum: {e}")
    
    logger.info(f"Generation complete. Total: {num_matrices}, Success: {len(df)}, Skipped: {skipped_count}")
    
    return df

def main():
    """Main entry point for the synthetic attention data generation script."""
    config = get_config()
    num_matrices = getattr(config, 'NUM_MATRICES', 1000) # Default from config, can be overridden
    
    # Ensure data/raw directory exists
    project_root = get_project_root()
    output_path = project_root / "data" / "raw" / "synthetic_attention_matrices.csv"
    
    logger.info(f"Generating {num_matrices} matrices to {output_path}")
    
    df = generate_static_dataset(
        num_matrices=num_matrices,
        output_path=output_path,
        seed_base=42
    )
    
    # Verification
    if len(df) != num_matrices:
        logger.warning(f"Generated {len(df)} matrices, expected {num_matrices}. Some were skipped.")
    else:
        logger.info(f"Successfully generated {len(df)} matrices as expected.")
        
    # Verify required columns exist
    required_cols = ['mean', 'variance', 'sparsity', 'outlier_magnitude', 'scaling_factor']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)
        
    # Verify no NaN in scaling_factor
    if df['scaling_factor'].isna().any():
        logger.error("Dataset contains NaN values in scaling_factor column.")
        sys.exit(1)
        
    logger.info("Data generation and verification complete.")

if __name__ == "__main__":
    main()
