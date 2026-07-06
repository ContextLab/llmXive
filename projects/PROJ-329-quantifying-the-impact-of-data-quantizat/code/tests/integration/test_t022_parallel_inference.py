import os
import sys
import tempfile
import json
import h5py
import numpy as np
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.inference_engine import InferenceConfig, run_batch_inference, load_signal_data

class TestT022ParallelInference:
    """Integration test for T022: Parallel execution strategy."""

    @pytest.fixture
    def mock_dataset_path(self, tmp_path):
        """Create a mock HDF5 dataset for testing."""
        dataset_path = tmp_path / "waveforms_pilot_test.h5"
        
        with h5py.File(dataset_path, 'w') as f:
            # Create 10 mock signals
            for i in range(10):
                grp = f.create_group(f"signal_{i}")
                grp.create_dataset('data', data=np.random.randn(1024))
                grp.create_dataset('noise', data=np.random.randn(1024))
                grp.attrs['sampling_frequency'] = 1024.0
                grp.attrs['chirp_mass'] = 30.0 + i
                grp.attrs['distance'] = 400.0 + i * 10
                grp.attrs['spin'] = 0.0 + i * 0.1
                grp.attrs['snr'] = 20.0 + i
                grp.attrs['bit_depth'] = 8
                grp.attrs['snr_bin'] = "14-20"
        
        return dataset_path

    def test_parallel_execution_runs(self, mock_dataset_path):
        """Test that parallel execution completes without errors."""
        config = InferenceConfig(
            n_steps=10,  # Small number for test speed
            n_walkers=5,
            max_cores=2,
            random_seed=42
        )
        
        output_path = mock_dataset_path.parent / "results_test.json"
        
        # Run inference
        results = run_batch_inference(mock_dataset_path, config, output_path)
        
        # Verify results
        assert len(results) == 10
        assert output_path.exists()
        
        # Verify JSON structure
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == 10
            
            for item in data:
                assert 'signal_id' in item
                assert 'posterior_mean' in item
                assert 'converged' in item

    def test_single_signal_load(self, mock_dataset_path):
        """Test loading a single signal."""
        data = load_signal_data(mock_dataset_path, "signal_0")
        
        assert data['id'] == "signal_0"
        assert len(data['quantized_data']) == 1024
        assert data['true_params']['chirp_mass'] == 30.0
        assert data['quantization_depth'] == 8
        
    def test_concurrency_limit(self, mock_dataset_path):
        """Test that max_cores limit is respected."""
        config = InferenceConfig(
            n_steps=10,
            n_walkers=5,
            max_cores=1, # Force single core
            random_seed=42
        )
        
        output_path = mock_dataset_path.parent / "results_single_core.json"
        results = run_batch_inference(mock_dataset_path, config, output_path)
        
        assert len(results) == 10
        assert output_path.exists()

    def test_missing_file_handling(self, tmp_path):
        """Test handling of missing input file."""
        config = InferenceConfig()
        missing_path = tmp_path / "nonexistent.h5"
        
        with pytest.raises(FileNotFoundError):
            run_batch_inference(missing_path, config)

    def test_invalid_signal_id(self, mock_dataset_path):
        """Test handling of invalid signal ID."""
        with pytest.raises(KeyError):
            load_signal_data(mock_dataset_path, "invalid_id")
