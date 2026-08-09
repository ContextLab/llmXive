import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from loops.base_zppo import StaticZPPOLoop, StaticNCQGenerator
from loops.cap_zppo import CAPZPPOLoop, CAPNCQGenerator
from models.state_store import StateStore
from models.student_sim import SimulatedStudent
from config import get_config

@pytest.fixture
def mock_config():
    return {
        'simulation': {
            'num_cycles': 5,
            'noise_sigma': 0.05,
            'min_candidates': 1
        },
        'negative_candidates': ['A', 'B', 'C', 'D'],
        'seed': {'seed': 42}
    }

@pytest.fixture
def mock_held_out_data():
    return [
        {'question': 'Q1', 'answer': 'A'},
        {'question': 'Q2', 'answer': 'B'},
        {'question': 'Q3', 'answer': 'C'},
        {'question': 'Q4', 'answer': 'D'},
        {'question': 'Q5', 'answer': 'A'}
    ]

@pytest.fixture
def state_store():
    return StateStore()

@pytest.fixture
def student_mock():
    mock = Mock(spec=SimulatedStudent)
    mock.predict_confidence.return_value = 0.75
    mock.update_state = Mock()
    mock.reset = Mock()
    return mock

def test_static_loop_noise_injection(mock_config, mock_held_out_data, state_store, student_mock):
    """Test that StaticZPPOLoop injects Gaussian noise into confidence scores."""
    loop = StaticZPPOLoop(mock_config, state_store)
    loop.student = student_mock
    loop.held_out_data = mock_held_out_data
    loop.ncq_generator = StaticNCQGenerator(mock_held_out_data, mock_config)
    
    # Run one cycle
    np.random.seed(42) # Reset seed for deterministic noise check
    result = loop.run_one_cycle(0)
    
    base_conf = student_mock.predict_confidence.return_value
    # The result confidence should not be exactly the base confidence due to noise
    # We verify it's within a reasonable range (base +/- 3*sigma)
    assert result['confidence'] != base_conf, "Confidence should be modified by noise"
    
    # Check that noise was applied (sigma=0.05)
    # With seed 42, the noise is deterministic
    np.random.seed(42)
    expected_noise = np.random.normal(0, mock_config['simulation']['noise_sigma'])
    expected_conf = np.clip(base_conf + expected_noise, 0.0, 1.0)
    
    assert np.isclose(result['confidence'], expected_conf), f"Expected {expected_conf}, got {result['confidence']}"

def test_cap_loop_noise_injection(mock_config, mock_held_out_data, state_store, student_mock):
    """Test that CAPZPPOLoop injects Gaussian noise into confidence scores."""
    loop = CAPZPPOLoop(mock_config, state_store)
    loop.student = student_mock
    loop.held_out_data = mock_held_out_data
    loop.ncq_generator = CAPNCQGenerator(mock_held_out_data, mock_config, state_store)
    
    # Run one cycle
    np.random.seed(42)
    result = loop.run_one_cycle(0)
    
    base_conf = student_mock.predict_confidence.return_value
    assert result['confidence'] != base_conf, "Confidence should be modified by noise"
    
    # Verify noise application
    np.random.seed(42)
    expected_noise = np.random.normal(0, mock_config['simulation']['noise_sigma'])
    expected_conf = np.clip(base_conf + expected_noise, 0.0, 1.0)
    
    assert np.isclose(result['confidence'], expected_conf), f"Expected {expected_conf}, got {result['confidence']}"

def test_noise_clipping(mock_config, mock_held_out_data, state_store, student_mock):
    """Test that noise injection respects [0, 1] bounds."""
    loop = StaticZPPOLoop(mock_config, state_store)
    loop.student = student_mock
    loop.held_out_data = mock_held_out_data
    loop.ncq_generator = StaticNCQGenerator(mock_held_out_data, mock_config)
    
    # Force base confidence to be very low
    student_mock.predict_confidence.return_value = 0.02
    np.random.seed(1) # Seed that produces negative noise
    result = loop.run_one_cycle(0)
    
    assert result['confidence'] >= 0.0, "Confidence should not be below 0"
    assert result['confidence'] <= 1.0, "Confidence should not be above 1"
    
    # Force base confidence to be very high
    student_mock.predict_confidence.return_value = 0.98
    np.random.seed(2) # Seed that produces positive noise
    result = loop.run_one_cycle(0)
    
    assert result['confidence'] >= 0.0, "Confidence should not be below 0"
    assert result['confidence'] <= 1.0, "Confidence should not be above 1"

def test_noise_sigma_parameter(mock_config, mock_held_out_data, state_store, student_mock):
    """Test that the noise_sigma parameter is used correctly."""
    # Test with different sigma
    mock_config['simulation']['noise_sigma'] = 0.1
    loop = StaticZPPOLoop(mock_config, state_store)
    loop.student = student_mock
    loop.held_out_data = mock_held_out_data
    loop.ncq_generator = StaticNCQGenerator(mock_held_out_data, mock_config)
    
    base_conf = 0.5
    student_mock.predict_confidence.return_value = base_conf
    
    # Run multiple times to estimate variance
    np.random.seed(123)
    deviations = []
    for _ in range(100):
        result = loop.run_one_cycle(0)
        deviations.append((result['confidence'] - base_conf) ** 2)
    
    estimated_variance = np.mean(deviations)
    expected_variance = mock_config['simulation']['noise_sigma'] ** 2
    
    # Allow some tolerance for estimation
    assert abs(estimated_variance - expected_variance) < 0.005, \
        f"Variance mismatch: estimated {estimated_variance}, expected {expected_variance}"