import pytest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path

from data_generation.synthetic_attention import (
    generate_static_attention_matrix,
    generate_static_dataset,
    SyntheticMatrixStats
)
from data_generation.sinkhorn_solver import SingleStepSinkhornSolver

def test_synthetic_generation_schema():
    """Test that generated matrices have the correct statistical properties."""
    matrix, stats = generate_static_attention_matrix(
        shape=(32, 32),
        target_sparsity=0.2,
        outlier_fraction=0.05,
        outlier_magnitude_factor=5.0,
        seed=123
    )
    
    # Check matrix shape
    assert matrix.shape == (32, 32)
    
    # Check stats types
    assert isinstance(stats, SyntheticMatrixStats)
    assert isinstance(stats.mean, float)
    assert isinstance(stats.variance, float)
    assert isinstance(stats.sparsity, float)
    assert isinstance(stats.outlier_magnitude, float)
    
    # Check sparsity is close to target (allow some tolerance)
    assert 0.15 <= stats.sparsity <= 0.25, f"Sparsity {stats.sparsity} not in expected range"
    
    # Check non-negativity of variance
    assert stats.variance >= 0
    
    # Check non-negativity of outlier magnitude
    assert stats.outlier_magnitude >= 0

def test_drift_parameters_applied():
    """Test that the generation process applies parameters correctly."""
    # Test with high sparsity
    _, stats_high_sparse = generate_static_attention_matrix(
        shape=(64, 64),
        target_sparsity=0.5,
        outlier_fraction=0.01,
        outlier_magnitude_factor=10.0,
        seed=456
    )
    
    # Test with low sparsity
    _, stats_low_sparse = generate_static_attention_matrix(
        shape=(64, 64),
        target_sparsity=0.05,
        outlier_fraction=0.01,
        outlier_magnitude_factor=10.0,
        seed=789
    )
    
    # High sparsity should result in higher sparsity ratio
    assert stats_high_sparse.sparsity > stats_low_sparse.sparsity

def test_dataset_generation():
    """Test the full dataset generation pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_dataset.csv"
        
        df = generate_static_dataset(
            num_matrices=10,
            matrix_shape=(16, 16),
            target_sparsity=0.1,
            outlier_fraction=0.02,
            outlier_magnitude_factor=5.0,
            output_path=output_path,
            seed_base=999
        )
        
        # Check number of rows
        assert len(df) == 10, f"Expected 10 rows, got {len(df)}"
        
        # Check columns
        expected_cols = ['index', 'mean', 'variance', 'sparsity', 'outlier_magnitude', 'scaling_factor']
        assert list(df.columns) == expected_cols
        
        # Check no NaN in scaling_factor
        assert not df['scaling_factor'].isna().any()
        
        # Check file was created
        assert output_path.exists()
        
        # Check file is not empty
        assert output_path.stat().st_size > 0

def test_scaling_factor_computation():
    """Test that scaling factors are computed correctly."""
    matrix, _ = generate_static_attention_matrix(
        shape=(16, 16),
        seed=111
    )
    
    solver = SingleStepSinkhornSolver()
    scaling_factor = solver.solve(matrix, epsilon=1e-6)
    
    assert isinstance(scaling_factor, float)
    assert np.isfinite(scaling_factor)
    assert scaling_factor > 0
