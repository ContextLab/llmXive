"""
Unit tests for microstate template application logic.
Specifically tests the Global Explained Variance (GEV) threshold constraint.
"""
import numpy as np
import pytest
import sys
import os

# Add project root to path to allow imports from code/
# Assuming this test runs from the project root or tests/unit/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.microstate import load_microstate_template, apply_microstate_template
from code.entities import MicrostateSegmentation

# Constants for testing
EXPECTED_GEVS_THRESHOLD = 0.75  # 75%
NUM_SUBJECTS = 5
NUM_CHANNELS = 32
NUM_TIMEPOINTS = 1000
NUM_CLASSES = 4

def generate_synthetic_eeg_data():
    """
    Generates synthetic EEG data that is perfectly correlated with a template
    to ensure GEV is high (close to 1.0) for a passing test.
    In a real scenario, this would load preprocessed EEG from data/processed.
    """
    # Create a "perfect" template signal
    base_signal = np.random.randn(NUM_TIMEPOINTS)
    # Create channels as linear combinations of the base signal + small noise
    # This ensures the data is well-explained by a few components
    data = np.zeros((NUM_CHANNELS, NUM_TIMEPOINTS))
    weights = np.random.randn(NUM_CHANNELS, 1)
    
    for i in range(NUM_CHANNELS):
        data[i] = weights[i, 0] * base_signal + np.random.normal(0, 0.01, NUM_TIMEPOINTS)
    
    return data

def generate_mock_template():
    """
    Generates a mock microstate template (4 classes, 32 channels).
    In production, this is loaded from data/templates/microstate_template.npy (T016A).
    """
    # Template shape: (num_classes, num_channels)
    # Random orthogonal-like vectors to serve as class topographies
    template = np.random.randn(NUM_CLASSES, NUM_CHANNELS)
    # Normalize topographies to unit norm
    template = template / np.linalg.norm(template, axis=1, keepdims=True)
    return template

@pytest.fixture(scope="module")
def mock_template():
    """Load or generate the template used for testing."""
    # In a real integration, we would load the file from disk.
    # For this unit test, we generate a deterministic mock if file missing.
    template_path = os.path.join(project_root, 'data', 'templates', 'microstate_template.npy')
    if os.path.exists(template_path):
        return np.load(template_path)
    else:
        return generate_mock_template()

def test_microstate_template_application_gev(mock_template):
    """
    T011: Unit test for microstate template application (GEV ≥75%).
    
    Verifies that when applying the template to EEG data that is structurally
    similar to the template, the Global Explained Variance (GEV) meets the
    minimum threshold of 75% as required by the specification.
    """
    # Prepare data
    eeg_data = generate_synthetic_eeg_data()
    
    # Apply the template
    # Expected signature based on T016B: apply_microstate_template(eeg_data, template)
    result = apply_microstate_template(eeg_data, mock_template)
    
    # Verify return type
    assert isinstance(result, MicrostateSegmentation), \
        f"Expected MicrostateSegmentation, got {type(result)}"
    
    # Verify GEV metric
    gev = result.gev
    assert gev is not None, "GEV should not be None"
    
    # Assert GEV meets the threshold (>= 0.75)
    assert gev >= EXPECTED_GEVS_THRESHOLD, \
        f"GEV {gev:.4f} is below the required threshold of {EXPECTED_GEVS_THRESHOLD}. " \
        "Template application failed to explain sufficient variance."
    
    # Verify label assignment shape
    assert result.labels.shape == (NUM_TIMEPOINTS,), \
        f"Labels shape {result.labels.shape} does not match expected timepoints {NUM_TIMEPOINTS}"
    
    # Verify labels are within expected class range (0 to 3 for 4 classes)
    assert np.all((result.labels >= 0) & (result.labels < NUM_CLASSES)), \
        "Labels contain values outside the valid class range [0, 3]"

def test_microstate_template_application_empty_data(mock_template):
    """
    Test handling of empty or invalid data inputs.
    """
    empty_data = np.zeros((NUM_CHANNELS, 0))
    
    # Depending on implementation, this might raise an error or return empty result.
    # We assert it handles it gracefully (either by raising ValueError or returning valid empty object).
    try:
        result = apply_microstate_template(empty_data, mock_template)
        # If it doesn't raise, it should return a valid object with empty labels
        assert isinstance(result, MicrostateSegmentation)
        assert result.labels.size == 0
    except ValueError as e:
        # Acceptable behavior: raise specific error for empty input
        assert "empty" in str(e).lower() or "size" in str(e).lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])