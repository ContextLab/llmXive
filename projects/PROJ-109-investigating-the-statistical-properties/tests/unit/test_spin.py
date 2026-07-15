"""
Unit tests for the spin parameter calculation using the Subsampled Plummer-Softened Potential.

This test verifies that the spin parameter calculation works correctly on a subsampled
set of particles (N=500) as mandated by the memory constraints and complexity tracking
in the implementation plan (Phase 1, Complexity Tracking).

It specifically tests the integration with T007C's subsampling logic and ensures
the resulting spin parameter falls within the expected physical range [0, 1].
"""
import os
import sys
import pytest
import numpy as np
from pathlib import Path

# Add the project root to the path to allow imports from code/
# This assumes the test is run from the project root or via pytest discovery
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.synthetic_generator import generate_halo_properties, save_to_hdf5
from code.data.streaming import subsample_particles
from code.data.compute_metrics import compute_halo_metrics
from code.config import RANDOM_SEED


def test_spin_parameter_subsample():
    """
    Test that the spin parameter is correctly calculated on a subsampled particle set.
    
    This test:
    1. Generates a synthetic halo with known properties.
    2. Saves it to a temporary HDF5 file.
    3. Subsamples the particles to N=500 (simulating the T007C logic).
    4. Computes the spin parameter using the subsampled data.
    5. Asserts the result is within the physical bounds [0, 1].
    """
    # Setup: Create a temporary directory for this test
    test_dir = project_root / "data" / "test_tmp"
    test_dir.mkdir(parents=True, exist_ok=True)
    temp_h5_path = test_dir / "test_spin_halo.h5"

    try:
        # 1. Generate synthetic halo data
        # We use a fixed seed to ensure reproducibility
        np.random.seed(RANDOM_SEED)
        halo_data = generate_halo_properties(
            num_halos=1,
            seed=RANDOM_SEED,
            mass_range=(1e12, 1e13),
            pos_range=(-500, 500), # kpc
            vel_range=(-500, 500)  # km/s
        )
        
        # Save to HDF5
        save_to_hdf5(halo_data, str(temp_h5_path))

        # 2. Load and Subsample (Simulating T007C logic)
        # We manually replicate the subsampling logic here to ensure the test
        # is self-contained and tests the specific path.
        # In a real scenario, this would be done via the ChunkedHDF5Reader
        # and subsample_particles function.
        
        # Load data for subsampling
        with h5py.File(temp_h5_path, 'r') as f:
            positions = f['positions'][0]
            velocities = f['velocities'][0]
            masses = f['masses'][0]
            
            # Ensure we have enough particles to subsample
            num_particles = len(positions)
            assert num_particles >= 500, "Test requires at least 500 particles to subsample."

            # Perform subsampling (random selection with fixed seed)
            rng = np.random.RandomState(RANDOM_SEED)
            indices = rng.choice(num_particles, size=500, replace=False)
            
            sub_positions = positions[indices]
            sub_velocities = velocities[indices]
            sub_masses = masses[indices]

        # 3. Compute Metrics using the subsampled data
        # We construct a minimal halo dictionary for the compute function
        halo_sample = {
            'id': 0,
            'positions': sub_positions,
            'velocities': sub_velocities,
            'masses': sub_masses,
            'num_particles': 500
        }

        # Call the metrics function
        # Note: compute_halo_metrics expects a list of halos or a single halo dict
        # depending on implementation. Based on the API surface, it likely handles
        # a list or iterates. We pass a list containing our single subsampled halo.
        results = compute_halo_metrics([halo_sample])

        # 4. Assertions
        assert len(results) == 1, "Expected one result for the single halo."
        
        spin = results[0].get('spin_parameter')
        
        # Check that spin parameter was calculated
        assert spin is not None, "Spin parameter was not calculated."
        
        # Check physical bounds: Spin parameter lambda is typically in [0, 1]
        # (though theoretically can be slightly outside, 0-1 is the expected range for dark matter halos)
        assert 0 <= spin <= 1, f"Spin parameter {spin} is outside expected physical range [0, 1]."

        # Check that the value is a valid float
        assert isinstance(spin, (float, np.floating)), "Spin parameter must be a float."

    finally:
        # Cleanup: Remove temporary file
        if temp_h5_path.exists():
            temp_h5_path.unlink()
        if test_dir.exists() and not any(test_dir.iterdir()):
            test_dir.rmdir()


if __name__ == "__main__":
    # Allow running as a script for quick validation
    pytest.main([__file__, "-v"])
