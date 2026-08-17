import pytest
import numpy as np
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
# We need to ensure the path is set up correctly if running standalone
# Assuming standard project structure
sys_path = Path(__file__).parent.parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from inference.mcmc import compute_gelman_rubin, run_mcmc
from config import ProjectConfig

class TestGelmanRubin:
    def test_converged_chains(self):
        """Test with chains that are well mixed (GR ~ 1.0)"""
        # Create 4 walkers, 100 steps, 2 params
        # All chains have similar mean and variance
        n_walkers, n_steps, n_params = 4, 100, 2
        samples = np.random.randn(n_walkers, n_steps, n_params) * 0.1
        # Add a small offset to means to test sensitivity
        samples += 0.01 * np.arange(n_walkers).reshape(-1, 1, 1)
        
        gr = compute_gelman_rubin(samples)
        assert gr < 1.1 # Should be close to 1.0
        
    def test_unconverged_chains(self):
        """Test with chains that are far apart (GR > 1.1)"""
        n_walkers, n_steps, n_params = 4, 100, 2
        samples = np.zeros((n_walkers, n_steps, n_params))
        
        # Walker 0 centered at 0
        samples[0] = np.random.randn(n_steps, n_params) * 0.1
        # Walker 1 centered at 10
        samples[1] = 10 + np.random.randn(n_steps, n_params) * 0.1
        # Walker 2 centered at 0
        samples[2] = np.random.randn(n_steps, n_params) * 0.1
        # Walker 3 centered at 10
        samples[3] = 10 + np.random.randn(n_steps, n_params) * 0.1
        
        gr = compute_gelman_rubin(samples)
        assert gr > 1.1 # Should be significantly > 1.0

@pytest.mark.integration
def test_run_mcmc_structure(tmp_path):
    """
    Test the structure of run_mcmc without running full MCMC (too slow).
    We mock the likelihood to ensure the loop logic works.
    """
    # Create a mock likelihood class
    class MockLikelihood:
        def __init__(self, *args, **kwargs):
            pass
        
        def log_prob(self, theta):
            # Return a simple quadratic to simulate convergence
            # -0.5 * (theta[0]**2 + theta[1]**2)
            # This is a simple Gaussian centered at 0,0
            return -0.5 * np.sum(theta**2)
    
    # Patch the import
    with patch('inference.mcmc.YukawaLikelihood', MockLikelihood):
        with patch('inference.mcmc.load_covariance_matrix'):
            with patch('inference.mcmc.Path.exists', return_value=True):
                # Create a minimal config
                config = ProjectConfig()
                # Override paths to tmp_path to avoid writing to real data dirs
                config.results_dir = str(tmp_path / "results")
                os.makedirs(config.results_dir, exist_ok=True)
                
                # Run a very short test
                # We force min_steps=10, batch=5, max=50 to test the loop logic
                # We expect it to run at least 10 steps
                try:
                    results = run_mcmc(
                        config, 
                        n_walkers=4, 
                        min_steps=10, 
                        batch_size=5, 
                        max_steps=50,
                        convergence_thresh=1.01 # Force it to run until max or convergence
                    )
                    
                    # Check that results dict has expected keys
                    assert "total_steps" in results
                    assert "converged" in results
                    assert "gelman_rubin" in results
                    assert results["total_steps"] >= 10
                    
                    # Check that files were created
                    samples_path = Path(config.results_dir) / "mcmc_samples.npy"
                    metadata_path = Path(config.results_dir) / "mcmc_run_metadata.json"
                    
                    assert samples_path.exists()
                    assert metadata_path.exists()
                    
                    # Verify metadata content
                    with open(metadata_path) as f:
                        meta = json.load(f)
                    assert meta["total_steps"] == results["total_steps"]
                    
                except Exception as e:
                    # If it fails due to actual MCMC issues (e.g. bad likelihood),
                    # we still want to check if the structure is there.
                    # But for this test, we assume the mock is good enough.
                    pytest.fail(f"MCMC runner failed: {e}")