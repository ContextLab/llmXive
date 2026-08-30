import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import from the project's utility module
from code.utils.fixation_detection import calculate_velocity, calculate_dispersion, detect_fixations_ivt

@pytest.fixture
def sample_gaze_data():
    # Simulate a fixation: points close together in space and time
    data = {
        'x': [100, 102, 101, 100, 101],
        'y': [200, 201, 200, 199, 200],
        'timestamp': [1000, 1033, 1066, 1100, 1133]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_moving_data():
    # Simulate a saccade: points far apart
    data = {
        'x': [100, 150, 200, 250],
        'y': [200, 200, 200, 200],
        'timestamp': [1000, 1033, 1066, 1100]
    }
    return pd.DataFrame(data)

def test_calculate_velocity_zero():
    # Two identical points
    df = pd.DataFrame({'x': [100, 100], 'y': [200, 200], 'timestamp': [1000, 1033]})
    velocities = calculate_velocity(df)
    assert np.all(velocities == 0)

def test_calculate_velocity_nonzero():
    # Points moving 50 pixels in 33ms
    df = pd.DataFrame({'x': [100, 150], 'y': [200, 200], 'timestamp': [1000, 1033]})
    velocities = calculate_velocity(df)
    # Distance = 50, Time = 33ms, Velocity = 50/33 pixels/ms
    expected_velocity = 50 / 33.0
    assert np.isclose(velocities[1], expected_velocity)

def test_calculate_dispersion():
    # Calculate dispersion for a set of points
    points_x = [100, 102, 101, 100, 101]
    points_y = [200, 201, 200, 199, 200]
    dispersion = calculate_dispersion(points_x, points_y)
    # Dispersion is the max distance between any two points
    # Max x diff = 2, Max y diff = 2, Euclidean distance = sqrt(2^2 + 2^2) = sqrt(8)
    expected_dispersion = np.sqrt(2**2 + 2**2)
    assert np.isclose(dispersion, expected_dispersion)

def test_detect_fixations_ivt_basic(sample_gaze_data):
    # Duration threshold 100ms, Dispersion threshold 30 pixels
    fixations = detect_fixations_ivt(sample_gaze_data, duration_threshold=100, dispersion_threshold=30)
    # The sample data represents a fixation (points close together, duration > 100ms)
    assert len(fixations) > 0
    # Check that the first fixation starts at the first timestamp
    assert fixations[0]['start_time'] == 1000

def test_detect_fixations_ivt_moving_data(sample_moving_data):
    # Moving data should result in few or no fixations with standard thresholds
    fixations = detect_fixations_ivt(sample_moving_data, duration_threshold=100, dispersion_threshold=30)
    # With high velocity, points won't cluster into fixations
    # Depending on implementation, might have 0 or very short fixations
    assert len(fixations) == 0 or all(f['duration'] < 100 for f in fixations)

def test_detect_fixations_ivt_zero_duration_threshold(sample_gaze_data):
    """Test edge case: 0ms duration threshold should accept any cluster meeting dispersion."""
    # With 0ms threshold, any group of points within dispersion threshold counts
    # Our sample data has low dispersion, so it should form a fixation
    fixations = detect_fixations_ivt(sample_gaze_data, duration_threshold=0, dispersion_threshold=30)
    assert len(fixations) > 0

def test_detect_fixations_ivt_undefined_time_threshold():
    """Test edge case: explicitly defined time threshold behavior."""
    # Create data with exactly the threshold duration
    data = {
        'x': [100, 100, 100],
        'y': [200, 200, 200],
        'timestamp': [1000, 1050, 1100]  # 100ms duration (1100 - 1000)
    }
    df = pd.DataFrame(data)
    # Threshold is exactly 100ms, duration is exactly 100ms -> should be included
    fixations = detect_fixations_ivt(df, duration_threshold=100, dispersion_threshold=30)
    assert len(fixations) == 1
    assert fixations[0]['duration'] == 100

def test_detect_fixations_ivt_below_threshold():
    """Test edge case: duration just below threshold should be excluded."""
    data = {
        'x': [100, 100, 100],
        'y': [200, 200, 200],
        'timestamp': [1000, 1050, 1099]  # 99ms duration
    }
    df = pd.DataFrame(data)
    fixations = detect_fixations_ivt(df, duration_threshold=100, dispersion_threshold=30)
    # Should be excluded because 99 < 100
    assert len(fixations) == 0
