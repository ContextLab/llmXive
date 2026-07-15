import os
import json
import numpy as np
import pytest
from pathlib import Path
from datetime import datetime

# Test imports
from data.simulate_EEG import WilsonCowanSimulator, simulate_eeg_for_subject, DEFAULT_WC_PARAMS
from config import get_data_root


class TestWilsonCowanSimulator:
    def test_initialization(self):
        """Test that simulator initializes with correct seed and params."""
        seed = 123
        params = DEFAULT_WC_PARAMS.copy()
        simulator = WilsonCowanSimulator(params, seed)
        
        assert simulator.seed == seed
        assert simulator.params == params
        assert simulator.rng is not None

    def test_simulate_returns_correct_shapes(self):
        """Test that simulation returns time vector and activity matrix of correct shapes."""
        seed = 42
        params = {
            "tau_e": 0.01,
            "tau_i": 0.02,
            "w_ee": 1.0,
            "w_ei": 1.0,
            "w_ie": 1.0,
            "w_ii": 1.0,
            "I_ext": 0.5,
            "dt": 0.001,
            "t_total": 1.0,
            "noise_sigma": 0.05
        }
        # Create a small test connectome
        connectome = np.ones((3, 3)) * 0.5
        np.fill_diagonal(connectome, 0.0)
        
        simulator = WilsonCowanSimulator(params, seed)
        time_vec, activity = simulator.simulate(connectome)
        
        expected_steps = int(params["t_total"] / params["dt"])
        assert time_vec.shape == (expected_steps,)
        assert activity.shape == (3, expected_steps)
        assert np.all((activity >= 0) & (activity <= 1))

    def test_firing_rate_monotonicity(self):
        """Test that firing rate function is monotonically increasing."""
        simulator = WilsonCowanSimulator(DEFAULT_WC_PARAMS, 42)
        x = np.linspace(-5, 5, 100)
        y = simulator._firing_rate(x)
        
        # Check monotonicity
        assert np.all(np.diff(y) >= -1e-6)  # Allow small numerical errors
        assert y[0] < y[-1]


class TestSimulationMetadata:
    def test_metadata_contains_required_fields(self):
        """Test that metadata dictionary contains all required reproducibility fields."""
        subject_id = "test_sub"
        seed = 999
        wc_params = DEFAULT_WC_PARAMS.copy()
        
        # Create a mock connectome file
        data_root = get_data_root()
        processed_dir = data_root / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        mock_connectome = np.eye(5)
        connectome_path = processed_dir / f"{subject_id}_connectome.npy"
        np.save(connectome_path, mock_connectome)
        
        try:
            meta = simulate_eeg_for_subject(
                subject_id=subject_id,
                output_dir=processed_dir,
                seed=seed,
                wc_params=wc_params
            )
            
            assert meta["subject_id"] == subject_id
            assert meta["random_seed"] == seed
            assert meta["status"] == "success"
            assert "wilson_cowan_params" in meta
            assert meta["wilson_cowan_params"] == wc_params
            assert "timestamp" in meta
            assert "n_nodes" in meta
            assert "sfreq_hz" in meta
            
        finally:
            # Cleanup
            if connectome_path.exists():
                connectome_path.unlink()
            eeg_path = processed_dir / f"{subject_id}_eeg.npy"
            if eeg_path.exists():
                eeg_path.unlink()
            time_path = processed_dir / f"{subject_id}_time.npy"
            if time_path.exists():
                time_path.unlink()

    def test_metadata_json_file_created(self):
        """Test that simulation_metadata.json is created with correct structure."""
        # This test assumes the main() function has been run or metadata is saved
        # For unit testing, we check the structure of the saved JSON
        data_root = get_data_root()
        metadata_path = data_root / "processed" / "simulation_metadata.json"
        
        if not metadata_path.exists():
            # If file doesn't exist, skip this test (it's integration-level)
            pytest.skip("simulation_metadata.json not found (expected if main() not run)")
            return

        with open(metadata_path, "r") as f:
            data = json.load(f)
        
        assert "pipeline" in data
        assert data["pipeline"] == "simulate_EEG"
        assert "master_seed" in data
        assert "timestamp" in data
        assert "total_subjects" in data
        assert "successful_subjects" in data
        assert "subjects" in data
        assert isinstance(data["subjects"], list)
        
        if len(data["subjects"]) > 0:
            first_subject = data["subjects"][0]
            assert "subject_id" in first_subject
            assert "random_seed" in first_subject
            assert "wilson_cowan_params" in first_subject
            assert "status" in first_subject
            assert first_subject["status"] in ["success", "failed"]

    def test_random_seed_reproducibility(self):
        """Test that same seed produces same results."""
        connectome = np.random.RandomState(42).rand(3, 3)
        np.fill_diagonal(connectome, 0.0)
        
        params = DEFAULT_WC_PARAMS.copy()
        seed = 12345
        
        sim1 = WilsonCowanSimulator(params, seed)
        _, activity1 = sim1.simulate(connectome)
        
        sim2 = WilsonCowanSimulator(params, seed)
        _, activity2 = sim2.simulate(connectome)
        
        assert np.allclose(activity1, activity2)