import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import time

# Import from existing project API
from data_generation.sinkhorn_solver import SingleStepSinkhornSolver, SinkhornNonConvergenceError
from data_generation.utils import apply_epsilon_floor, check_numerical_stability
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SyntheticMatrixStats:
    """Dataclass to hold statistics for a generated synthetic attention matrix."""
    mean: float
    variance: float
    sparsity: float
    outlier_magnitude: float
    scaling_factor: Optional[float]
    convergence_status: str  # 'converged', 'non_converged', 'failed'
    generation_time_ms: float

def generate_static_attention_matrix(
    shape: Tuple[int, int],
    sparsity: float,
    outlier_magnitude: float,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generates a synthetic attention matrix with controlled sparsity and outlier magnitudes.
    
    Args:
        shape: Tuple (rows, cols) for the matrix dimensions.
        sparsity: Fraction of elements to be zeroed out (0.0 to 1.0).
        outlier_magnitude: Scale factor for outlier values.
        seed: Optional random seed for reproducibility.
        
    Returns:
        np.ndarray: The generated attention matrix.
    """
    if seed is not None:
        np.random.seed(seed)
        
    rows, cols = shape
    
    # 1. Generate base Gaussian matrix
    matrix = np.random.randn(rows, cols).astype(np.float32)
    
    # 2. Apply sparsity (zero out random elements)
    mask = np.random.random((rows, cols)) > sparsity
    matrix = matrix * mask
    
    # 3. Inject outliers
    # Determine number of outliers based on matrix size
    num_outliers = max(1, int(rows * cols * 0.01))  # 1% outliers
    outlier_indices = np.random.choice(rows * cols, num_outliers, replace=False)
    outlier_rows = outlier_indices // cols
    outlier_cols = outlier_indices % cols
    
    # Inject outliers with specified magnitude
    outlier_values = np.random.randn(num_outliers).astype(np.float32) * outlier_magnitude
    matrix[outlier_rows, outlier_cols] = outlier_values
    
    # 4. Ensure numerical stability (apply epsilon floor to prevent div/0 later)
    # Note: The actual epsilon floor for the solver is applied inside the solver
    # or by the caller, but we ensure the base matrix is not pathological
    matrix = apply_epsilon_floor(matrix, epsilon=1e-9)
    
    return matrix

def compute_scaling_factor(
    matrix: np.ndarray,
    solver: SingleStepSinkhornSolver,
    epsilon: float
) -> Tuple[Optional[float], str]:
    """
    Computes the ground-truth scaling factor using the SingleStepSinkhornSolver.
    
    Args:
        matrix: The attention matrix to process.
        solver: Instance of SingleStepSinkhornSolver.
        epsilon: Epsilon parameter for the solver.
        
    Returns:
        Tuple of (scaling_factor, status) where status is 'converged', 'non_converged', or 'failed'.
    """
    try:
        # Check for NaN/Inf in input
        if not check_numerical_stability(matrix):
            return None, "failed"
            
        scaling_factor = solver.solve(matrix, epsilon)
        
        if np.isnan(scaling_factor) or np.isinf(scaling_factor):
            return None, "non_converged"
            
        return float(scaling_factor), "converged"
        
    except SinkhornNonConvergenceError:
        return None, "non_converged"
    except Exception as e:
        logger.warning(f"Unexpected error during scaling factor computation: {e}")
        return None, "failed"

def generate_static_dataset(
    num_matrices: int,
    matrix_shape: Tuple[int, int],
    sparsity_range: Tuple[float, float],
    outlier_range: Tuple[float, float],
    epsilon: float,
    output_path: str,
    seed: Optional[int] = None
) -> None:
    """
    Generates a dataset of synthetic attention matrices with ground-truth scaling factors.
    
    Args:
        num_matrices: Number of matrices to generate.
        matrix_shape: Shape of each matrix (rows, cols).
        sparsity_range: Tuple (min_sparsity, max_sparsity) for random sampling.
        outlier_range: Tuple (min_outlier, max_outlier) for random sampling.
        epsilon: Epsilon parameter for the Sinkhorn solver.
        output_path: Path to save the output Parquet file.
        seed: Base seed for reproducibility.
    """
    if seed is not None:
        np.random.seed(seed)
        
    logger.info(f"Starting generation of {num_matrices} matrices...")
    
    # Initialize solver
    solver = SingleStepSinkhornSolver()
    
    # Prepare storage for results
    results = []
    successful_count = 0
    failed_count = 0
    
    start_time = time.time()
    
    for i in range(num_matrices):
        # Sample parameters
        sparsity = np.random.uniform(*sparsity_range)
        outlier_magnitude = np.random.uniform(*outlier_range)
        current_seed = i if seed is None else seed + i
        
        # Generate matrix
        matrix = generate_static_attention_matrix(
            matrix_shape, sparsity, outlier_magnitude, seed=current_seed
        )
        
        # Compute statistics
        matrix_mean = float(np.mean(matrix))
        matrix_var = float(np.var(matrix))
        matrix_sparsity = float(np.mean(matrix == 0))
        matrix_outlier_mag = float(outlier_magnitude)
        
        # Compute scaling factor
        start_solve = time.time()
        scaling_factor, status = compute_scaling_factor(matrix, solver, epsilon)
        solve_time_ms = (time.time() - start_solve) * 1000
        
        if status == "converged":
            successful_count += 1
            results.append({
                'matrix_mean': matrix_mean,
                'matrix_var': matrix_var,
                'matrix_sparsity': matrix_sparsity,
                'matrix_outlier_magnitude': matrix_outlier_mag,
                'scaling_factor': scaling_factor,
                'convergence_status': status,
                'generation_time_ms': solve_time_ms
            })
        else:
            failed_count += 1
            # We still record the stats but mark scaling_factor as NaN/None
            # The task says "skip or flag" - we flag by recording the row with None
            results.append({
                'matrix_mean': matrix_mean,
                'matrix_var': matrix_var,
                'matrix_sparsity': matrix_sparsity,
                'matrix_outlier_magnitude': matrix_outlier_mag,
                'scaling_factor': None,
                'convergence_status': status,
                'generation_time_ms': solve_time_ms
            })
            
        # Progress logging
        if (i + 1) % 1000 == 0:
            logger.info(f"Processed {i + 1}/{num_matrices} matrices. "
                        f"Successful: {successful_count}, Failed: {failed_count}")
    
    total_time = time.time() - start_time
    logger.info(f"Generation complete in {total_time:.2f} seconds.")
    logger.info(f"Total: {num_matrices}, Successful: {successful_count}, Failed: {failed_count}")
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to Parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Dataset saved to {output_path}")
    
    # Verification
    assert len(df) == num_matrices, f"Expected {num_matrices} rows, got {len(df)}"
    assert 'scaling_factor' in df.columns, "Missing scaling_factor column"
    assert 'matrix_mean' in df.columns, "Missing matrix_mean column"
    
    logger.info(f"Verification passed: {len(df)} rows saved.")

def main():
    """Main entry point for the data generation script."""
    config = get_config()
    
    # Configuration from config.py or defaults
    num_matrices = config.NUM_MATRICES if hasattr(config, 'NUM_MATRICES') else 10000
    matrix_size = 128
    matrix_shape = (matrix_size, matrix_size)
    
    # Sparsity range: 0.0 (dense) to 0.9 (sparse)
    sparsity_min = 0.0
    sparsity_max = 0.9
    sparsity_range = (sparsity_min, sparsity_max)
    
    # Outlier magnitude range
    outlier_min = 1.0
    outlier_max = 10.0
    outlier_range = (outlier_min, outlier_max)
    
    # Epsilon from config
    epsilon = config.EPSILON_FLOOR if hasattr(config, 'EPSILON_FLOOR') else 1e-6
    
    # Output path
    output_path = "data/raw/synthetic_attention_matrices.parquet"
    
    # Seed
    seed = config.RANDOM_SEED if hasattr(config, 'RANDOM_SEED') else 42
    
    logger.info(f"Configuration: num_matrices={num_matrices}, shape={matrix_shape}, "
                f"sparsity_range={sparsity_range}, outlier_range={outlier_range}, "
                f"epsilon={epsilon}, seed={seed}")
                
    generate_static_dataset(
        num_matrices=num_matrices,
        matrix_shape=matrix_shape,
        sparsity_range=sparsity_range,
        outlier_range=outlier_range,
        epsilon=epsilon,
        output_path=output_path,
        seed=seed
    )

if __name__ == "__main__":
    main()