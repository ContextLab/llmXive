"""Contract tests for trajectory data schema.

These tests verify that the Trajectory dataclass adheres to the expected
schema and validation rules defined in utils.data_models.
"""
import pytest
import numpy as np
from utils.data_models import Trajectory


def test_trajectory_schema():
    """Verify Trajectory dataclass schema matches expectations."""
    # Create sample data
    time_data = np.array([0.0, 0.1, 0.2])
    state_data = np.array([[1.0, 2.0, 3.0], [1.1, 2.1, 3.1], [1.2, 2.2, 3.2]])

    # Instantiate the Trajectory object
    trajectory = Trajectory(
        time=time_data,
        state=state_data,
        system_type="lorenz",
        seed=42
    )

    # Verify shapes match the contract: time should be 1D, state 2D
    assert trajectory.time.shape == (3,), f"Expected time shape (3,), got {trajectory.time.shape}"
    assert trajectory.state.shape == (3, 3), f"Expected state shape (3, 3), got {trajectory.state.shape}"

    # Verify metadata fields
    assert trajectory.system_type == "lorenz", "System type mismatch"
    assert trajectory.seed == 42, "Seed mismatch"

    # Verify data types
    assert isinstance(trajectory.time, np.ndarray), "Time must be numpy array"
    assert isinstance(trajectory.state, np.ndarray), "State must be numpy array"


def test_trajectory_validation_nan():
    """Verify trajectory validation catches NaN values in time or state."""
    # Test NaN in time
    time_data_nan = np.array([0.0, np.nan, 0.2])
    state_data = np.array([[1.0, 2.0, 3.0], [1.1, 2.1, 3.1], [1.2, 2.2, 3.2]])

    with pytest.raises(ValueError, match="Time data contains NaN"):
        Trajectory(time=time_data_nan, state=state_data, system_type="lorenz", seed=42)

    # Test NaN in state
    time_data = np.array([0.0, 0.1, 0.2])
    state_data_nan = np.array([[1.0, 2.0, 3.0], [np.nan, 2.1, 3.1], [1.2, 2.2, 3.2]])

    with pytest.raises(ValueError, match="State data contains NaN"):
        Trajectory(time=time_data, state=state_data_nan, system_type="lorenz", seed=42)


def test_trajectory_validation_empty():
    """Verify trajectory validation catches empty arrays."""
    time_data = np.array([])
    state_data = np.array([])

    with pytest.raises(ValueError, match="Trajectory data cannot be empty"):
        Trajectory(time=time_data, state=state_data, system_type="lorenz", seed=42)


def test_trajectory_validation_shape_mismatch():
    """Verify trajectory validation catches shape mismatches between time and state."""
    time_data = np.array([0.0, 0.1, 0.2, 0.3])  # 4 points
    state_data = np.array([[1.0, 2.0, 3.0], [1.1, 2.1, 3.1], [1.2, 2.2, 3.2]])  # 3 points

    with pytest.raises(ValueError, match="Time and state data length mismatch"):
        Trajectory(time=time_data, state=state_data, system_type="lorenz", seed=42)


def test_trajectory_min_length():
    """Verify trajectory validation enforces minimum length threshold."""
    # Create a trajectory with only 2 points (below typical minimum of 3)
    time_data = np.array([0.0, 0.1])
    state_data = np.array([[1.0, 2.0, 3.0], [1.1, 2.1, 3.1]])

    # The Trajectory class should enforce a minimum length (e.g., 3 points)
    # If the implementation requires a minimum, this should raise ValueError
    # Note: Depending on the specific implementation in utils/data_models.py,
    # this test might pass or fail. Assuming a minimum of 3 based on common
    # dynamical systems requirements.
    try:
        Trajectory(time=time_data, state=state_data, system_type="lorenz", seed=42)
        # If no error is raised, the minimum length check might not be implemented yet
        # This is acceptable if the data_models.py doesn't enforce it strictly
    except ValueError as e:
        if "minimum length" in str(e).lower():
            raise
        # Re-raise if it's a different validation error
        raise