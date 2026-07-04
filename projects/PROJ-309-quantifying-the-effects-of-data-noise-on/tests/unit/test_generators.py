import pytest
import numpy as np

from code.generators import generate_lorenz_trajectory, generate_rossler_trajectory, validate_trajectory

def test_lorenz_generation():
    traj = generate_lorenz_trajectory(seed=42, t_end=1.0)
    assert traj.system_type == "lorenz"
    assert traj.seed == 42
    assert len(traj.t) > 0
    assert traj.state.shape[0] == len(traj.t)
    assert not np.any(np.isnan(traj.state))

def test_rossler_generation():
    traj = generate_rossler_trajectory(seed=42, t_end=1.0)
    assert traj.system_type == "rossler"
    assert traj.seed == 42
    assert len(traj.t) > 0
    assert traj.state.shape[0] == len(traj.t)
    assert not np.any(np.isnan(traj.state))

def test_validate_trajectory():
    traj = generate_lorenz_trajectory(seed=42, t_end=1.0)
    assert validate_trajectory(traj) is True

    # Test with invalid data
    bad_traj = type('BadTraj', (), {
        'system_type': 'test',
        'seed': 1,
        't': np.array([1, 2, 3]),
        'state': np.array([[1, 2, 3], [np.nan, 0, 0], [1, 2, 3]]),
        'params': {}
    })()
    with pytest.raises(ValueError):
        validate_trajectory(bad_traj)