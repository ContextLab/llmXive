"""
Tests for simulate_EEG.py (T011).
"""
import os
import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.simulate_EEG import WilsonCowanSimulator, load_connectome, simulate_eeg_for_subject
from config import SIMULATION_PARAMS

class TestWilsonCowanSimulator:
    """Unit tests for the Wilson-Cowan simulator."""

    def test_initialization(self):
        """Test that the simulator initializes correctly."""
        adj = np.eye(3)
        params = {'dt': 0.1, 't_steps': 100}
        sim = WilsonCowanSimulator(adj, params)
        assert sim.n_nodes == 3
        assert sim.dt == 0.1
        assert sim.t_steps == 100

    def test_sigmoid_output_range(self):
        """Test that sigmoid output is between 0 and 1."""
        adj = np.eye(2)
        params = {'dt': 0.1, 't_steps': 10}
        sim = WilsonCowanSimulator(adj, params)

        # Test sigmoid with various inputs
        test_inputs = np.array([-10, -5, 0, 5, 10])
        outputs = sim.sigmoid(test_inputs)
        assert np.all(outputs >= 0)
        assert np.all(outputs <= 1)

    def test_simulation_runs(self):
        """Test that the simulation runs without error and produces output."""
        adj = np.array([[0, 0.5], [0.5, 0]])
        params = {
            'dt': 0.1,
            't_steps': 50,
            'noise_level': 0.01,
            'w_exc': 1.0,
            'w_inh': -0.5,
            'tau_e': 20.0,
            'tau_i': 10.0
        }
        sim = WilsonCowanSimulator(adj, params)
        result = sim.run_simulation()

        assert result.shape == (2, 50)
        assert np.all(result >= 0)  # Activity should be non-negative

    def test_normalization(self):
        """Test that adjacency matrix is normalized correctly."""
        # Create a matrix with large values
        adj = np.array([[0, 100], [100, 0]])
        params = {'dt': 0.1, 't_steps': 10}
        sim = WilsonCowanSimulator(adj, params)

        # Max value should be <= 1 after normalization
        assert np.max(np.abs(sim.adj_matrix)) <= 1.0

class TestLoadConnectome:
    """Tests for the connectome loading function."""

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a non-existent file returns None."""
        result = load_connectome("sub-999", tmp_path)
        assert result is None

    def test_load_valid_connectome(self, tmp_path):
        """Test loading a valid connectome file."""
        # Create a dummy connectome directory
        conn_dir = tmp_path / "processed" / "connectomes"
        conn_dir.mkdir(parents=True)

        # Create a dummy connectome file
        adj = np.array([[0, 0.5], [0.5, 0]])
        df = pd.DataFrame(adj)
        df.to_csv(conn_dir / "sub-001_connectome.csv", index=False, header=False)

        result = load_connectome("sub-001", tmp_path)
        assert result is not None
        assert result.shape == (2, 2)
        np.testing.assert_array_almost_equal(result, adj)

class TestSimulateEEGIntegration:
    """Integration tests for the full EEG simulation pipeline."""

    def test_full_pipeline(self, tmp_path):
        """Test the full simulation pipeline with dummy data."""
        # Setup
        conn_dir = tmp_path / "processed" / "connectomes"
        conn_dir.mkdir(parents=True)

        # Create a small dummy connectome
        adj = np.array([[0, 0.3, 0.2], [0.3, 0, 0.4], [0.2, 0.4, 0]])
        df = pd.DataFrame(adj)
        df.to_csv(conn_dir / "sub-001_connectome.csv", index=False, header=False)

        output_dir = tmp_path / "processed" / "eeg"
        output_dir.mkdir(parents=True)

        params = {
            'dt': 0.1,
            't_steps': 100,
            'noise_level': 0.01,
            'target_fs': 250
        }

        # Run simulation
        result_path = simulate_eeg_for_subject(
            subject_id="sub-001",
            data_root=tmp_path,
            output_dir=output_dir,
            params=params
        )

        # Verify output
        assert result_path is not None
        assert result_path.exists()

        # Check CSV output
        csv_path = output_dir / "sub-001_eeg.csv"
        assert csv_path.exists()

        # Verify CSV content
        data = pd.read_csv(csv_path)
        assert data.shape[1] == 3  # 3 nodes
        assert data.shape[0] > 0  # Some time steps

    def test_handles_missing_connectome(self, tmp_path):
        """Test that the pipeline handles missing connectome gracefully."""
        output_dir = tmp_path / "processed" / "eeg"
        output_dir.mkdir(parents=True)

        result = simulate_eeg_for_subject(
            subject_id="sub-999",
            data_root=tmp_path,
            output_dir=output_dir,
            params={'target_fs': 250}
        )

        assert result is None