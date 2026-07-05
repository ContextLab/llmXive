"""
Unit test for Menger sponge ground truth.

Verifies that the box-counting algorithm computes a fractal dimension (D_f)
for a synthetic Menger sponge that matches the theoretical value (D = log(20)/log(3) ≈ 2.7268)
within a tolerance of ±0.05.

This test relies on `validation/synthetic_menger.py` to generate the ground truth data.
"""
import numpy as np
import pytest
from pathlib import Path
import sys
import os

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from validation.synthetic_menger import generate_menger_sponge
from analysis.fractal import compute_box_counting_dimension

# Theoretical fractal dimension of a Menger sponge: log(20)/log(3)
THEORETICAL_D_MENGER = np.log(20) / np.log(3)
TOLERANCE = 0.05

def test_menger_sponge_ground_truth():
    """
    Test that the computed fractal dimension of a Menger sponge matches
    the theoretical value within the specified tolerance.
    """
    # Configuration for the synthetic sponge
    # Iteration 4 provides a good balance between resolution and computation time
    # for unit testing purposes.
    iteration = 4
    voxels_per_side = 3 ** iteration  # 81
    
    # Generate the Menger sponge data (1 for solid, 0 for void)
    sponge_grid = generate_menger_sponge(iteration)
    
    assert sponge_grid.shape[0] == voxels_per_side
    assert sponge_grid.shape[1] == voxels_per_side
    assert sponge_grid.shape[2] == voxels_per_side
    assert np.all((sponge_grid == 0) | (sponge_grid == 1))

    # Compute the fractal dimension using the box-counting algorithm
    # We use a range of box sizes appropriate for the grid resolution.
    # The algorithm should return a value close to THEORETICAL_D_MENGER.
    
    try:
        computed_d_f = compute_box_counting_dimension(sponge_grid)
    except Exception as e:
        pytest.fail(f"compute_box_counting_dimension raised an exception: {e}")

    # Assert the result is within tolerance
    assert abs(computed_d_f - THEORETICAL_D_MENGER) <= TOLERANCE, (
        f"Computed D_f ({computed_d_f:.4f}) differs from theoretical "
        f"value ({THEORETICAL_D_MENGER:.4f}) by more than {TOLERANCE}. "
        f"Error: {abs(computed_d_f - THEORETICAL_D_MENGER):.4f}"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])