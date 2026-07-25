"""
Static synthetic attention matrix generator for KVarN research.

Generates independent 128x128 attention matrices with controlled sparsity and
outlier magnitudes, computes ground-truth scaling factors using the SingleStepSinkhornSolver,
and saves the dataset to Parquet format.

Output: data/generated/static_matrices.parquet
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time
from dataclasses import dataclass, asdict
import json

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data_generation.sinkhorn_solver import SingleStepSinkhornSolver
from code.data_generation.utils import apply_epsilon_floor, check_numerical_stability
from code.config import get_config
from code.utils.seeds import set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SyntheticMatrixStats:
    """Statistics for a generated synthetic attention matrix."""
    matrix_id: int
    mean: float
    var: float
    sparsity: float
    outlier_magnitude: float
    scaling_factor: float
    generation_time_ms: float
    solver_status: str  # 'converged', 'failed', 'nan'

def generate_static_attention_matrix(
    size: int = 128,
    target_sparsity: float = 0.1,
    outlier_fraction: float = 0.05,
    outlier_magnitude_range: Tuple[float, float] = (5.0, 10.0),
    seed: Optional[int] = None
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Generate a single static attention matrix with controlled properties.
    
    Args:
        size: Matrix dimension (default 128x128)
        target_sparsity: Fraction of zero elements
        outlier_fraction: Fraction of extreme outlier values
        outlier_magnitude_range: (min, max) magnitude for outliers
        seed: Optional seed for reproducibility (uses global seed if None)
    
    Returns:
        Tuple of (matrix, stats_dict)
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Start with random Gaussian values
    matrix = np.random.randn(size, size).astype(np.float64)
    
    # Apply sparsity mask
    num_zeros = int(size * size * target_sparsity)
    zero_indices = np.random.choice(size * size, num_zeros, replace=False)
    matrix.flat[zero_indices] = 0.0
    
    # Add outliers
    num_outliers = int(size * size * outlier_fraction)
    if num_outliers > 0:
        outlier_indices = np.random.choice(
            size * size, num_outliers, replace=False
        )
        # Ensure we don't overwrite zeros with outliers
        outlier_indices = outlier_indices[zero_indices.max() + 1:] if num_zeros > 0 else outlier_indices
        outlier_indices = outlier_indices[:num_outliers]  # Re-trim if needed
        
        magnitudes = np.random.uniform(
            outlier_magnitude_range[0],
            outlier_magnitude_range[1],
            num_outliers
        )
        signs = np.random.choice([-1, 1], num_outliers)
        matrix.flat[outlier_indices] = magnitudes * signs
    
    # Compute statistics
    non_zero_mask = matrix != 0
    actual_sparsity = 1.0 - (np.sum(non_zero_mask) / (size * size))
    actual_mean = float(np.mean(matrix[non_zero_mask])) if np.any(non_zero_mask) else 0.0
    actual_var = float(np.var(matrix[non_zero_mask])) if np.any(non_zero_mask) else 0.0
    
    # Find max absolute value for outlier magnitude estimate
    actual_outlier_mag = float(np.max(np.abs(matrix[non_zero_mask]))) if np.any(non_zero_mask) else 0.0
    
    stats = {
        'mean': actual_mean,
        'var': actual_var,
        'sparsity': actual_sparsity,
        'outlier_magnitude': actual_outlier_mag
    }
    
    return matrix, stats

def compute_scaling_factor(
    matrix: np.ndarray,
    solver: SingleStepSinkhornSolver,
    epsilon_floor: float = 1e-6
) -> Tuple[float, str]:
    """
    Compute ground-truth scaling factor using SingleStepSinkhornSolver.
    
    Args:
        matrix: Attention matrix
        solver: Sinkhorn solver instance
        epsilon_floor: Epsilon floor for numerical stability
    
    Returns:
        Tuple of (scaling_factor, status)
    """
    try:
        # Apply epsilon floor to variance for stability
        var = np.var(matrix)
        var_safe = apply_epsilon_floor(var, epsilon_floor)
        
        # Run solver
        result = solver.solve(matrix, epsilon=epsilon_floor)
        
        # Check for convergence issues
        if np.isnan(result) or np.isinf(result):
            return float('nan'), 'nan'
        
        return float(result), 'converged'
        
    except Exception as e:
        logger.warning(f"Solver failed: {e}")
        return float('nan'), 'failed'

def generate_static_dataset(
    num_matrices: int = 10000,
    size: int = 128,
    target_sparsity: float = 0.1,
    outlier_fraction: float = 0.05,
    outlier_magnitude_range: Tuple[float, float] = (5.0, 10.0),
    epsilon_floor: float = 1e-6,
    output_path: Optional[Path] = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a dataset of static synthetic attention matrices.
    
    Args:
        num_matrices: Number of matrices to generate (must be 10000 for MVP)
        size: Matrix dimension
        target_sparsity: Target sparsity level
        outlier_fraction: Fraction of outlier values
        outlier_magnitude_range: Range for outlier magnitudes
        epsilon_floor: Epsilon floor for numerical stability
        output_path: Path to save Parquet file
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with matrix statistics and scaling factors
    """
    # Validate input
    if num_matrices != 10000:
        logger.warning(f"Requested {num_matrices} matrices, but MVP requires 10000. Adjusting.")
        num_matrices = 10000
    
    # Set global seed
    set_global_seed(seed)
    
    # Initialize solver
    solver = SingleStepSinkhornSolver()
    
    # Prepare storage
    records = []
    start_time = time.time()
    
    logger.info(f"Generating {num_matrices} static attention matrices...")
    
    for i in range(num_matrices):
        step_start = time.time()
        
        # Generate matrix
        matrix, stats = generate_static_attention_matrix(
            size=size,
            target_sparsity=target_sparsity,
            outlier_fraction=outlier_fraction,
            outlier_magnitude_range=outlier_magnitude_range,
            seed=seed + i  # Deterministic per-matrix seed
        )
        
        # Compute scaling factor
        scaling_factor, status = compute_scaling_factor(
            matrix, solver, epsilon_floor
        )
        
        # Validate numerical stability
        if not check_numerical_stability(scaling_factor):
            logger.warning(f"Matrix {i}: Scaling factor {scaling_factor} is not numerically stable")
            status = 'nan'
            scaling_factor = float('nan')
        
        # Record results
        record = {
            'matrix_id': i,
            'mean': stats['mean'],
            'var': stats['var'],
            'sparsity': stats['sparsity'],
            'outlier_magnitude': stats['outlier_magnitude'],
            'scaling_factor': scaling_factor,
            'generation_time_ms': (time.time() - step_start) * 1000,
            'solver_status': status
        }
        records.append(record)
        
        # Progress logging
        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            logger.info(f"Generated {i + 1}/{num_matrices} matrices ({rate:.1f} matrices/sec)")
    
    total_time = time.time() - start_time
    logger.info(f"Generated {num_matrices} matrices in {total_time:.2f}s ({num_matrices/total_time:.1f} matrices/sec)")
    
    # Create DataFrame
    df = pd.DataFrame(records)
    
    # Validate count
    assert len(df) == 10000, f"Expected 10000 rows, got {len(df)}"
    
    # Validate schema
    required_cols = ['mean', 'var', 'sparsity', 'outlier_magnitude', 'scaling_factor']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Save to Parquet if output_path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved dataset to {output_path}")
        
        # Log summary statistics
        logger.info(f"Dataset summary:")
        logger.info(f"  - Total rows: {len(df)}")
        logger.info(f"  - Mean scaling factor: {df['scaling_factor'].mean():.4f}")
        logger.info(f"  - Std scaling factor: {df['scaling_factor'].std():.4f}")
        logger.info(f"  - NaN scaling factors: {df['scaling_factor'].isna().sum()}")
        logger.info(f"  - Convergence rate: {(df['solver_status'] == 'converged').sum() / len(df) * 100:.1f}%")
    
    return df

def main():
    """Main entry point for static matrix generation."""
    config = get_config()
    
    output_path = Path(config.DATA_DIR) / 'generated' / 'static_matrices.parquet'
    
    df = generate_static_dataset(
        num_matrices=10000,
        size=128,
        target_sparsity=0.1,
        outlier_fraction=0.05,
        outlier_magnitude_range=(5.0, 10.0),
        epsilon_floor=config.EPSILON_FLOOR,
        output_path=output_path,
        seed=config.RANDOM_SEED
    )
    
    # Final validation
    assert len(df) == 10000, "Dataset must contain exactly 10000 matrices"
    assert output_path.exists(), "Output file must be created"
    
    logger.info("T017a completed successfully: 10000 static matrices generated")
    return df

if __name__ == '__main__':
    main()
