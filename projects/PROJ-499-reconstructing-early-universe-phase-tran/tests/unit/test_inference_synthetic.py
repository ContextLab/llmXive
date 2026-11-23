import pytest
import os
import json
import numpy as np
import tempfile
from pathlib import Path

# Mock healpy and dynesty for unit testing if necessary, 
# but since we are testing the logic, we might need to mock the heavy parts.
# However, for a unit test of the function logic, we can mock the external calls.
# But the task requires a real script that writes to disk.
# This test will check that the function runs without error on a mock input.

# We will mock the healpy and dynesty imports to avoid heavy computation in unit tests
# or we can run a very small scale test.
# Given the constraints, let's mock the heavy libraries.

@pytest.fixture
def mock_healpy(monkeypatch):
    import types
    mock_hp = types.ModuleType('healpy')
    mock_hp.read_map = lambda x, field=None, h=False: (np.array([1.0]), {})
    mock_hp.anafast = lambda x, lmax=None, pol=False: (np.array([1.0]),)
    mock_hp.map2alm = lambda x: np.array([1.0])
    monkeypatch.setattr('inference.hp', mock_hp)
    return mock_hp

@pytest.fixture
def mock_dynesty(monkeypatch):
    import types
    mock_dynesty = types.ModuleType('dynesty')
    mock_nested_sampler = types.ModuleType('NestedSampler')
    
    class MockSampler:
        def __init__(self, *args, **kwargs):
            pass
        def run_nested(self, *args, **kwargs):
            pass
        @property
        def results(self):
            class MockResults:
                samples = np.array([[0.0]]) # log_r = 0 => r=1
                weights = np.array([1.0])
                logz = [-10.0]
                logzerr = [0.1]
            return MockResults()
    
    mock_dynesty.NestedSampler = MockSampler
    mock_dynesty.utils = types.ModuleType('utils')
    mock_dynesty.utils.resample_equal = lambda samples, weights: samples
    monkeypatch.setattr('inference.dynesty', mock_dynesty)
    return mock_dynesty

def test_run_inference_synthetic_creates_output(mock_healpy, mock_dynesty, monkeypatch):
    """
    Test that run_inference_synthetic creates the output JSON file.
    """
    # Create a temporary directory for test artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        input_fits = os.path.join(tmpdir, 'test_inflation.fits')
        output_json = os.path.join(tmpdir, 'test_results.json')
        ground_truth_json = os.path.join(tmpdir, 'ground_truth_inflation.json')
        
        # Create a mock ground truth JSON
        gt_data = {
            'l_values': [2, 3, 4],
            'cl_bb_template_r1': [0.1, 0.2, 0.3],
            'cl_bb_sigma': [0.01, 0.02, 0.03]
        }
        with open(ground_truth_json, 'w') as f:
            json.dump(gt_data, f)
        
        # Create a dummy FITS file (just a file for the test)
        # In reality, this would be a FITS, but we mock the reader.
        with open(input_fits, 'w') as f:
            f.write('dummy fits content')
        
        # Import the function (it will use the mocked modules)
        from inference import run_inference_synthetic
        
        # Run the function
        results = run_inference_synthetic(input_fits, output_json)
        
        # Verify output file exists
        assert os.path.exists(output_json), "Output JSON file was not created"
        
        # Verify content
        with open(output_json, 'r') as f:
            saved_results = json.load(f)
        
        assert 'posterior_mean_r' in saved_results
        assert 'credible_interval_95_r' in saved_results
        assert 'log_evidence' in saved_results
        
        # Check that the function returned the results
        assert results == saved_results