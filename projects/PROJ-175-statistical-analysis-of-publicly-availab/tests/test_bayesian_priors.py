"""
Tests for T304: Refine Bayesian Priors for Proxy Data.
Verifies that priors are adjusted based on the amendment log methodology.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Mock the amendment log for testing
@pytest.fixture
def mock_amendment_log(tmp_path):
    log_path = tmp_path / "data" / "amendment_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Test Case 1: Correlational Analysis (Proxy)
    with open(log_path, 'w') as f:
        json.dump({
            "status": "RATIFIED",
            "methodology": "Correlational Analysis",
            "proxy_source": "Recipe1M",
            "timestamp": "2023-10-27T12:00:00"
        }, f)
    return log_path

@pytest.fixture
def mock_amendment_log_causal(tmp_path):
    log_path = tmp_path / "data" / "amendment_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Test Case 2: Causal Independence
    with open(log_path, 'w') as f:
        json.dump({
            "status": "RATIFIED",
            "methodology": "Causal Independence",
            "proxy_source": None,
            "timestamp": "2023-10-27T12:00:00"
        }, f)
    return log_path

@pytest.fixture
def mock_training_data(tmp_path):
    data_path = tmp_path / "data" / "processed" / "train.csv"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create minimal valid dataset
    data = {
        'log_co_occurrence': [1.0, 2.0, 3.0, 4.0, 5.0],
        'flavor_similarity': [0.1, 0.5, 0.8, 0.2, 0.9],
        'functional_role': [2, 1, 0, 2, 1],
        'compatibility_label': [1, 0, 1, 0, 1]
    }
    df = pd.DataFrame(data)
    df.to_csv(data_path, index=False)
    return data_path

def test_prior_sigma_proxy(mock_amendment_log, mock_training_data, tmp_path):
    """
    Test that when methodology is 'Correlational Analysis', 
    the prior sigma is set to the wider value (3.0).
    """
    # Temporarily override the path for the module
    import sys
    from unittest.mock import patch
    
    # We need to test the logic inside get_prior_sigma or the main flow
    # Since the module loads from a fixed path, we mock the load_amendment_log function
    
    from code.models import bayesian
    
    # Mock the load_amendment_log to return our test data
    def mock_load():
        return {
            "methodology": "Correlational Analysis"
        }
    
    with patch.object(bayesian, 'load_amendment_log', mock_load):
        sigma = bayesian.get_prior_sigma("Correlational Analysis")
        assert sigma == 3.0, f"Expected prior sigma 3.0 for proxy data, got {sigma}"

def test_prior_sigma_causal(mock_amendment_log_causal, mock_training_data, tmp_path):
    """
    Test that when methodology is 'Causal Independence',
    the prior sigma is set to the standard value (1.0).
    """
    from code.models import bayesian
    
    sigma = bayesian.get_prior_sigma("Causal Independence")
    assert sigma == 1.0, f"Expected prior sigma 1.0 for causal data, got {sigma}"

def test_prior_config_file_generation(mock_amendment_log, mock_training_data, tmp_path):
    """
    Test that the prior_config.json file is generated with correct values.
    """
    from code.models import bayesian
    import json
    
    # Setup paths
    output_dir = tmp_path / "data" / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock data
    X = np.array([[1.0, 0.1], [2.0, 0.5]])
    y = np.array([1, 0])
    predictors = ['log_co_occurrence', 'flavor_similarity']
    
    # Mock the model fitting to avoid actual sampling in tests
    class MockTrace:
        pass
    
    class MockSummary:
        mean = {'beta_0': 0.5, 'beta_1': 0.2}
        hdi_94_ = {'beta_0': [0.1, 0.9], 'beta_1': [-0.1, 0.5]}
    
    with patch.object(bayesian, 'fit_bayesian_model', return_value=(MockTrace(), MockSummary())):
        with patch.object(bayesian, 'load_amendment_log', return_value={"methodology": "Correlational Analysis"}):
            # Call the function that saves results
            # We simulate the flow by calling save_results directly with the expected sigma
            results, config = bayesian.save_results(
                MockSummary(), 
                str(output_dir), 
                "Correlational Analysis", 
                3.0
            )
            
            # Verify config file content
            config_path = output_dir / "prior_config.json"
            assert config_path.exists(), "prior_config.json was not created"
            
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
            
            assert saved_config['methodology'] == "Correlational Analysis"
            assert saved_config['prior_sigma'] == 3.0
            assert "uncertainty" in saved_config['rationale'].lower()

def test_model_fallback_logic(mock_amendment_log, mock_training_data):
    """
    Test that the model handles the proxy methodology gracefully.
    """
    # This is a structural test to ensure the code path exists
    from code.models import bayesian
    
    # Verify the constants are set correctly
    assert bayesian.DEFAULT_PRIOR_SIGMA_PROXY > bayesian.DEFAULT_PRIOR_SIGMA_CAUSAL
    assert bayesian.DEFAULT_PRIOR_SIGMA_PROXY == 3.0
    assert bayesian.DEFAULT_PRIOR_SIGMA_CAUSAL == 1.0