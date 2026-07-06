import os
import sys
import tempfile
import shutil
import json
import h5py
import numpy as np
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data_generation import generate_dataset, record_state
from src.state_manager import load_state_file, verify_artifact_integrity

class TestT016DatasetGeneration:
    """
    Integration tests for T016: Save output dataset to HDF5 format.
    """
    
    def setup_method(self):
        """
        Setup temporary directory for test outputs.
        """
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create necessary directory structure
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(parents=True, exist_ok=True)
        
    def teardown_method(self):
        """
        Cleanup temporary directory.
        """
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_h5_file_creation(self):
        """
        Verify that the script creates a valid HDF5 file.
        """
        seed = 42
        output_path = generate_dataset(
            n_signals=5, # Small batch for testing
            bit_depths=[8, 16],
            snr_bins=[(8, 14), (30, 50)],
            seed=seed,
            output_filename=f"test_waveforms_{seed}.h5"
        )
        
        assert Path(output_path).exists(), "Output file was not created"
        assert output_path.endswith('.h5'), "Output file is not HDF5 format"
        
        # Verify file is readable
        with h5py.File(output_path, 'r') as f:
            assert 'metadata' in f, "Metadata group missing"
            assert f['metadata'].attrs['seed'] == seed, "Seed mismatch in metadata"
    
    def test_file_size_limit(self):
        """
        Verify that the file size is within the 4GB limit (for pilot).
        """
        seed = 123
        output_path = generate_dataset(
            n_signals=10,
            bit_depths=[8, 10, 12, 14, 16],
            snr_bins=[(8, 14), (14, 20), (20, 30), (30, 50)],
            seed=seed,
            output_filename=f"test_size_{seed}.h5"
        )
        
        file_size = Path(output_path).stat().st_size
        file_size_gb = file_size / (1024**3)
        
        # For pilot (N=10 per bin), should be well under 4GB
        # Even with N=50, it should be under 4GB
        assert file_size_gb < 4.0, f"File size {file_size_gb:.2f}GB exceeds 4GB limit"
    
    def test_state_recording(self):
        """
        Verify that the state is recorded in state.yaml.
        """
        seed = 456
        output_path = generate_dataset(
            n_signals=5,
            bit_depths=[8],
            snr_bins=[(8, 14)],
            seed=seed,
            output_filename=f"test_state_{seed}.h5"
        )
        
        state = load_state_file()
        assert state is not None, "State file not created"
        assert 'phases' in state, "No phases in state"
        
        # Find the US1 phase
        us1_phase = None
        for phase in state['phases']:
            if phase.get('task') == 'T016':
                us1_phase = phase
                break
        
        assert us1_phase is not None, "T016 phase not found in state"
        assert len(us1_phase['artifacts']) > 0, "No artifacts recorded"
        
        artifact = us1_phase['artifacts'][0]
        assert artifact['path'] == output_path, "Artifact path mismatch"
        assert 'hash' in artifact, "Hash not recorded"
    
    def test_data_structure_integrity(self):
        """
        Verify that the HDF5 structure matches the expected schema.
        """
        seed = 789
        output_path = generate_dataset(
            n_signals=5,
            bit_depths=[16],
            snr_bins=[(20, 30)],
            seed=seed,
            output_filename=f"test_structure_{seed}.h5"
        )
        
        with h5py.File(output_path, 'r') as f:
            # Check metadata
            assert 'metadata' in f
            assert f['metadata'].attrs['n_signals'] == 5
            
            # Check dataset groups
            expected_group = "bit_16_snr_20_30"
            assert expected_group in f, f"Group {expected_group} missing"
            
            grp = f[expected_group]
            
            # Check required datasets
            required_datasets = [
                'times', 'h_plus', 'h_cross', 'injected_snr', 
                'actual_snr', 'mass1', 'mass2', 'distance', 
                'chirp_mass', 'fsr', 'baseline'
            ]
            
            for ds_name in required_datasets:
                assert ds_name in grp, f"Dataset {ds_name} missing"
            
            # Check shapes
            assert grp['times'].shape == (5, 8192), "Times shape mismatch"
            assert grp['h_plus'].shape == (5, 8192), "H_plus shape mismatch"
            assert grp['injected_snr'].shape == (5,), "Injected SNR shape mismatch"
            
            # Check data types
            assert grp['times'].dtype == np.float64, "Times dtype mismatch"
            assert grp['injected_snr'].dtype == np.float32, "Injected SNR dtype mismatch"
    
    def test_sn_range_coverage(self):
        """
        Verify that SNR values fall within the specified bins.
        """
        seed = 101
        snr_min, snr_max = 8, 14
        output_path = generate_dataset(
            n_signals=20,
            bit_depths=[8],
            snr_bins=[(snr_min, snr_max)],
            seed=seed,
            output_filename=f"test_snr_{seed}.h5"
        )
        
        with h5py.File(output_path, 'r') as f:
            grp = f['bit_8_snr_8_14']
            injected_snr = grp['injected_snr'][:]
            actual_snr = grp['actual_snr'][:]
            
            # Check that injected SNR is within range
            assert np.all(injected_snr >= snr_min), "Injected SNR below minimum"
            assert np.all(injected_snr <= snr_max), "Injected SNR above maximum"
            
            # Check that actual SNR is close to injected (tolerance)
            # Allow some variance due to noise injection
            tolerance = 1.0
            assert np.all(actual_snr >= snr_min - tolerance), "Actual SNR below range"
            assert np.all(actual_snr <= snr_max + tolerance), "Actual SNR above range"
    
    def test_quantization_levels(self):
        """
        Verify that quantized signals have discrete levels.
        """
        seed = 202
        bit_depth = 8
        output_path = generate_dataset(
            n_signals=5,
            bit_depths=[bit_depth],
            snr_bins=[(30, 50)],
            seed=seed,
            output_filename=f"test_quant_{seed}.h5"
        )
        
        with h5py.File(output_path, 'r') as f:
            grp = f['bit_8_snr_30_50']
            h_plus = grp['h_plus'][:]
            
            # Flatten and find unique values
            unique_vals = np.unique(h_plus)
            
            # For 8-bit, we expect at most 256 levels, but due to clipping and
            # signal dynamics, it might be less. We just check it's not continuous.
            # A continuous float array would have N unique values.
            # With quantization, it should be significantly less.
            max_levels = 2 ** bit_depth
            assert len(unique_vals) <= max_levels, f"Too many unique levels: {len(unique_vals)} > {max_levels}"
            
            # Also verify that levels are discrete (gaps exist)
            diffs = np.diff(unique_vals)
            min_diff = np.min(diffs[diffs > 0])
            assert min_diff > 1e-10, "Levels appear continuous, no quantization applied"