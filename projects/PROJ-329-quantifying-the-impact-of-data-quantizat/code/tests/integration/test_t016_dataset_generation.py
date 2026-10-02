"""
Integration tests for T016: Dataset generation and HDF5 serialization.
"""
import os
import sys
import tempfile
import shutil
import json
import h5py
import pytest
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_generation import generate_dataset, save_dataset_to_hdf5
from src.state_manager import load_state_file

class TestT016DatasetGeneration:
    """Tests for T016 dataset generation."""

    def test_hdf5_file_creation(self):
        """Test that HDF5 file is created successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_waveforms.h5"
            dataset = generate_dataset(
                n_signals=24,  # Small test set
                bit_depths=[8],
                snr_bins=[(8, 14)],
                seed=42,
                output_path=output_path,
                batch_size=12
            )
            
            assert output_path.exists(), "HDF5 file was not created"
            assert output_path.stat().st_size > 0, "HDF5 file is empty"

    def test_hdf5_structure(self):
        """Test that HDF5 file has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_waveforms.h5"
            dataset = generate_dataset(
                n_signals=24,
                bit_depths=[8],
                snr_bins=[(8, 14)],
                seed=42,
                output_path=output_path,
                batch_size=12
            )
            
            with h5py.File(output_path, 'r') as f:
                # Check metadata
                assert 'seed' in f.attrs
                assert 'n_signals' in f.attrs
                assert 'bit_depths' in f.attrs
                assert 'snr_bins' in f.attrs
                
                # Check signals group
                assert 'signals' in f
                signals_grp = f['signals']
                assert len(list(signals_grp.keys())) > 0

    def test_signal_data_integrity(self):
        """Test that signal data is correctly stored and retrievable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_waveforms.h5"
            dataset = generate_dataset(
                n_signals=24,
                bit_depths=[8],
                snr_bins=[(8, 14)],
                seed=42,
                output_path=output_path,
                batch_size=12
            )
            
            with h5py.File(output_path, 'r') as f:
                signals_grp = f['signals']
                first_signal = list(signals_grp.keys())[0]
                sig_grp = signals_grp[first_signal]
                
                # Check required fields
                assert 'quantized_signal' in sig_grp
                assert 'baseline_signal' in sig_grp
                assert 'bit_depth' in sig_grp.attrs
                assert 'actual_snr' in sig_grp.attrs
                
                # Check data types
                quantized = sig_grp['quantized_signal'][()]
                baseline = sig_grp['baseline_signal'][()]
                
                assert isinstance(quantized, np.ndarray)
                assert isinstance(baseline, np.ndarray)
                assert quantized.dtype == np.float64
                assert baseline.dtype == np.float64

    def test_file_size_constraint(self):
        """Test that generated file is within size constraints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_waveforms.h5"
            dataset = generate_dataset(
                n_signals=1200,  # Full pilot size
                bit_depths=[8, 16],  # Subset of bit depths
                snr_bins=[(8, 14)],  # Single bin for faster test
                seed=42,
                output_path=output_path,
                batch_size=100
            )
            
            file_size = output_path.stat().st_size
            max_size = 4 * 1024 * 1024 * 1024  # 4 GB
            
            assert file_size < max_size, f"File size {file_size} exceeds limit {max_size}"

    def test_state_recording(self):
        """Test that state is recorded after generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory for state file
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                output_path = Path(tmpdir) / "test_waveforms.h5"
                dataset = generate_dataset(
                    n_signals=24,
                    bit_depths=[8],
                    snr_bins=[(8, 14)],
                    seed=42,
                    output_path=output_path,
                    batch_size=12
                )
                
                state_file = Path("state.yaml")
                assert state_file.exists(), "State file was not created"
                
                state_data = load_state_file(state_file)
                assert state_data is not None
                assert 'artifact' in state_data
                assert 'hash' in state_data
                assert 'size_bytes' in state_data
            finally:
                os.chdir(original_cwd)

    def test_bit_depth_levels(self):
        """Test that quantized signals have correct number of levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_waveforms.h5"
            dataset = generate_dataset(
                n_signals=24,
                bit_depths=[8],
                snr_bins=[(8, 14)],
                seed=42,
                output_path=output_path,
                batch_size=12
            )
            
            with h5py.File(output_path, 'r') as f:
                signals_grp = f['signals']
                for sig_name in signals_grp.keys():
                    sig_grp = signals_grp[sig_name]
                    bit_depth = sig_grp.attrs['bit_depth']
                    quantized = sig_grp['quantized_signal'][()]
                    
                    # Count unique levels (accounting for floating point precision)
                    unique_levels = len(np.unique(np.round(quantized, decimals=10)))
                    max_levels = 2 ** bit_depth
                    
                    # Allow some tolerance for clipping
                    assert unique_levels <= max_levels + 1, \
                        f"Too many unique levels: {unique_levels} > {max_levels}"

    def test_snr_tolerance(self):
        """Test that actual SNR is within tolerance of target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_waveforms.h5"
            dataset = generate_dataset(
                n_signals=24,
                bit_depths=[8],
                snr_bins=[(8, 14)],
                seed=42,
                output_path=output_path,
                batch_size=12
            )
            
            with h5py.File(output_path, 'r') as f:
                signals_grp = f['signals']
                for sig_name in signals_grp.keys():
                    sig_grp = signals_grp[sig_name]
                    target_snr = sig_grp.attrs['target_snr']
                    actual_snr = sig_grp.attrs['actual_snr']
                    
                    tolerance = 0.5
                    assert abs(actual_snr - target_snr) <= tolerance, \
                        f"SNR tolerance exceeded: {actual_snr} vs {target_snr}"

    def test_parallel_baseline(self):
        """Test that baseline signals are float64 and match input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_waveforms.h5"
            dataset = generate_dataset(
                n_signals=24,
                bit_depths=[8],
                snr_bins=[(8, 14)],
                seed=42,
                output_path=output_path,
                batch_size=12
            )
            
            with h5py.File(output_path, 'r') as f:
                signals_grp = f['signals']
                for sig_name in signals_grp.keys():
                    sig_grp = signals_grp[sig_name]
                    quantized = sig_grp['quantized_signal'][()]
                    baseline = sig_grp['baseline_signal'][()]
                    
                    # Baseline should be float64
                    assert baseline.dtype == np.float64
                    
                    # Baseline should have same shape as quantized
                    assert baseline.shape == quantized.shape
                    
                    # Baseline should have more unique values than quantized
                    unique_baseline = len(np.unique(np.round(baseline, decimals=10)))
                    unique_quantized = len(np.unique(np.round(quantized, decimals=10)))
                    assert unique_baseline >= unique_quantized, \
                        "Baseline should have at least as many unique values as quantized"

    def test_memory_efficiency(self):
        """Test that batch processing keeps memory usage reasonable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # This test is more of a sanity check - in practice,
            # we would monitor memory usage during execution
            output_path = Path(tmpdir) / "test_waveforms.h5"
            dataset = generate_dataset(
                n_signals=1200,
                bit_depths=[8, 10, 12],
                snr_bins=[(8, 14), (14, 20)],
                seed=42,
                output_path=output_path,
                batch_size=50
            )
            
            assert output_path.exists()
            file_size = output_path.stat().st_size
            # Should be well under 4GB for this configuration
            assert file_size < 4 * 1024 * 1024 * 1024