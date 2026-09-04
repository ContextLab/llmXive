import pytest
import os
import json
import numpy as np
import tempfile
import shutil
from src.environment.synthetic_mdp import generate_mdp

class TestMDPNoiseLogging:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.makedirs(os.path.join(self.temp_dir, "data", "processed"), exist_ok=True)
        os.chdir(self.temp_dir)
        yield
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_correlation_logging_zero(self):
        """Test that no noise_properties.json is created when rho=0"""
        mdp = generate_mdp(n_objectives=5, seed=42, noise_correlation=0.0)
        json_path = os.path.join("data", "processed", "noise_properties.json")
        assert not os.path.exists(json_path)

    def test_correlation_logging_positive(self):
        """Test that noise_properties.json is created and contains valid data when rho > 0"""
        mdp = generate_mdp(n_objectives=5, seed=42, noise_correlation=0.5)
        json_path = os.path.join("data", "processed", "noise_properties.json")
        
        assert os.path.exists(json_path), "noise_properties.json should exist"
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list), "Data should be a list of entries"
        assert len(data) > 0, "Data should not be empty"
        
        entry = data[-1]
        assert entry["n_objectives"] == 5
        assert entry["target_rho"] == 0.5
        assert "summary" in entry
        assert "mean_off_diagonal" in entry["summary"]
        assert "diag_mean" in entry["summary"]
        
        # Verify the mean off-diagonal is close to 0.5 (allowing for numerical precision/adjustment)
        assert 0.4 < entry["summary"]["mean_off_diagonal"] < 0.6, \
            f"Mean off-diagonal {entry['summary']['mean_off_diagonal']} should be close to 0.5"

    def test_correlation_logging_multiple_runs(self):
        """Test that multiple runs append to the same file"""
        generate_mdp(n_objectives=5, seed=42, noise_correlation=0.2)
        generate_mdp(n_objectives=5, seed=43, noise_correlation=0.5)
        
        json_path = os.path.join("data", "processed", "noise_properties.json")
        assert os.path.exists(json_path)
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 2, "Should have 2 entries"
        assert data[0]["target_rho"] == 0.2
        assert data[1]["target_rho"] == 0.5