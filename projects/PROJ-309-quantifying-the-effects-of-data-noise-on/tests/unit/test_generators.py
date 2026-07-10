import pytest
import numpy as np
from code.generators import (
    generate_lorenz_trajectory,
    generate_rossler_trajectory,
    integrate_system,
    lorenz_system,
    rossler_system,
    validate_trajectory
)
from code.utils.data_models import Trajectory

def test_lorenz_trajectory_generation():
    """Test that Lorenz trajectory is generated with correct properties."""
    seed = 42
    trajectory = generate_lorenz_trajectory(seed=seed, t_end=10.0, dt=0.01)
    
    assert trajectory.system_type == 'lorenz'
    assert trajectory.seed == seed
    assert len(trajectory.t) > 0
    assert trajectory.state.shape[1] == 3  # 3 state variables
    assert not np.any(np.isnan(trajectory.state))
    assert not np.any(np.isinf(trajectory.state))

def test_rossler_trajectory_generation():
    """Test that Rössler trajectory is generated with correct properties."""
    seed = 123
    trajectory = generate_rossler_trajectory(seed=seed, t_end=10.0, dt=0.01)
    
    assert trajectory.system_type == 'rossler'
    assert trajectory.seed == seed
    assert len(trajectory.t) > 0
    assert trajectory.state.shape[1] == 3  # 3 state variables
    assert not np.any(np.isnan(trajectory.state))
    assert not np.any(np.isinf(trajectory.state))

def test_trajectory_validation_pass():
    """Test that a valid trajectory passes validation."""
    trajectory = Trajectory(
        system_type='lorenz',
        seed=42,
        t=np.linspace(0, 10, 1000),
        state=np.random.rand(1000, 3),
        params={'sigma': 10.0, 'rho': 28.0, 'beta': 8.0/3.0}
    )
    assert validate_trajectory(trajectory, min_length=1000) is True

def test_trajectory_validation_nan():
    """Test that a trajectory with NaN values fails validation."""
    trajectory = Trajectory(
        system_type='lorenz',
        seed=42,
        t=np.linspace(0, 10, 1000),
        state=np.random.rand(1000, 3),
        params={'sigma': 10.0, 'rho': 28.0, 'beta': 8.0/3.0}
    )
    trajectory.state[0, 0] = np.nan
    with pytest.raises(ValueError, match="NaN or Inf"):
        validate_trajectory(trajectory)

def test_trajectory_validation_too_short():
    """Test that a trajectory below minimum length fails validation."""
    trajectory = Trajectory(
        system_type='lorenz',
        seed=42,
        t=np.linspace(0, 1, 100),
        state=np.random.rand(100, 3),
        params={'sigma': 10.0, 'rho': 28.0, 'beta': 8.0/3.0}
    )
    with pytest.raises(ValueError, match="below minimum"):
        validate_trajectory(trajectory, min_length=1000)

def test_reproducibility():
    """Test that same seed produces same trajectory."""
    seed = 999
    t1, s1 = None, None
    t2, s2 = None, None
    
    traj1 = generate_lorenz_trajectory(seed=seed, t_end=5.0, dt=0.01)
    traj2 = generate_lorenz_trajectory(seed=seed, t_end=5.0, dt=0.01)
    
    assert np.allclose(traj1.t, traj2.t)
    assert np.allclose(traj1.state, traj2.state)

def test_lorenz_system_derivatives():
    """Test Lorenz system derivative calculation."""
    state = np.array([1.0, 1.0, 1.0])
    sigma, rho, beta = 10.0, 28.0, 8.0/3.0
    result = lorenz_system(0, state, sigma, rho, beta)
    
    # dx/dt = 10 * (1 - 1) = 0
    assert result[0] == 0.0
    # dy/dt = 1 * (28 - 1) - 1 = 26
    assert result[1] == 26.0
    # dz/dt = 1 * 1 - (8/3) * 1 = 1 - 8/3 = -5/3
    assert abs(result[2] - (-5.0/3.0)) < 1e-10

def test_rossler_system_derivatives():
    """Test Rössler system derivative calculation."""
    state = np.array([1.0, 0.0, 0.0])
    a, b, c = 0.2, 0.2, 5.7
    result = rossler_system(0, state, a, b, c)
    
    # dx/dt = -0 - 0 = 0
    assert result[0] == 0.0
    # dy/dt = 1 + 0.2 * 0 = 1
    assert result[1] == 1.0
    # dz/dt = 0.2 + 0 * (1 - 5.7) = 0.2
    assert result[2] == 0.2
