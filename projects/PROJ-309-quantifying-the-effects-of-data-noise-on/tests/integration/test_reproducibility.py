"""Integration tests for reproducibility across runs."""
import pytest
import numpy as np
from generators import generate_lorenz_trajectory
from config import get_seeds, get_system_params


@pytest.mark.integration
def test_reproducibility_lorenz_seed_stability():
    """Verify that same seed produces identical trajectories for Lorenz system.
    
    This test validates that the trajectory generation is deterministic given
    the same random seed and system parameters, which is critical for:
    1. Reproducible research results
    2. Controlled noise injection experiments
    3. Ground truth metric calculation consistency
    
    Expected: Trajectories from identical seeds should be bitwise identical.
    """
    seed = 42
    params = get_system_params("lorenz")
    
    # Run twice with same seed
    traj1 = generate_lorenz_trajectory(seed=seed, params=params)
    traj2 = generate_lorenz_trajectory(seed=seed, params=params)
    
    # Verify identical results
    np.testing.assert_array_almost_equal(
        traj1.time, 
        traj2.time,
        err_msg="Time arrays differ between runs with same seed"
    )
    np.testing.assert_array_almost_equal(
        traj1.state, 
        traj2.state,
        err_msg="State arrays differ between runs with same seed"
    )
    
    # Additional verification: check trajectory metadata
    assert traj1.metadata["seed"] == traj2.metadata["seed"]
    assert traj1.metadata["system_type"] == traj2.metadata["system_type"]


@pytest.mark.integration
def test_reproducibility_multiple_seeds():
    """Test reproducibility across multiple different seeds.
    
    Ensures that the seed stability holds for various seed values,
    not just a single case.
    """
    seeds = get_seeds()[:3]  # Test first 3 seeds from config
    
    for seed in seeds:
        with self.subTest(seed=seed):
            params = get_system_params("lorenz")
            
            traj1 = generate_lorenz_trajectory(seed=seed, params=params)
            traj2 = generate_lorenz_trajectory(seed=seed, params=params)
            
            np.testing.assert_array_almost_equal(traj1.time, traj2.time)
            np.testing.assert_array_almost_equal(traj1.state, traj2.state)


@pytest.mark.integration
def test_reproducibility_rossler_seed_stability():
    """Verify seed stability for Rössler system as well.
    
    While the primary focus is on Lorenz, we ensure the pattern holds
    for other chaotic systems in the pipeline.
    """
    from generators import generate_rossler_trajectory
    
    seed = 123
    params = get_system_params("rossler")
    
    traj1 = generate_rossler_trajectory(seed=seed, params=params)
    traj2 = generate_rossler_trajectory(seed=seed, params=params)
    
    np.testing.assert_array_almost_equal(traj1.time, traj2.time)
    np.testing.assert_array_almost_equal(traj1.state, traj2.state)