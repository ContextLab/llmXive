"""
Unit tests for T017 validation logic.
"""
import pytest
import numpy as np
import tempfile
import h5py
from pathlib import Path

from src.validate_quantization import verify_level_counts, validate_dataset


class TestVerifyLevelCounts:
    def test_8_bit_quantization(self):
        # Create a signal with exactly 256 levels (8-bit)
        levels = np.linspace(-1, 1, 256)
        signal = np.random.choice(levels, size=1000)
        is_valid, expected, actual = verify_level_counts(signal, 8)
        assert is_valid
        assert expected == 256
        assert actual == 256

    def test_8_bit_overflow(self):
        # Create a signal with 257 levels (should fail 8-bit check)
        levels = np.linspace(-1, 1, 257)
        signal = np.random.choice(levels, size=1000)
        is_valid, expected, actual = verify_level_counts(signal, 8)
        assert not is_valid
        assert expected == 256
        assert actual == 257

    def test_1_bit_quantization(self):
        # 1-bit should have 2 levels
        signal = np.random.choice([-1, 1], size=1000)
        is_valid, expected, actual = verify_level_counts(signal, 1)
        assert is_valid
        assert expected == 2
        assert actual == 2

    def test_clipping_effect(self):
        # If signal clips, it might have fewer levels than 2^N
        # This is acceptable (no more than 2^N)
        levels = np.linspace(-1, 1, 100)
        signal = np.random.choice(levels, size=1000)
        is_valid, expected, actual = verify_level_counts(signal, 8)
        assert is_valid  # 100 <= 256
        assert actual == 100


class TestValidateDataset:
    @pytest.fixture
    def sample_dataset(self):
        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as f:
            path = Path(f.name)
            with h5py.File(path, 'w') as hf:
                group = hf.create_group("signals")
                
                # Signal 1: Valid 8-bit
                sig1 = group.create_group("signal_001")
                data = sig1.create_dataset("quantized", data=np.random.choice(np.linspace(-1, 1, 256), 1000))
                data.attrs['bit_depth'] = 8
                data.attrs['target_snr'] = 20.0
                sig1.create_dataset("noise", data=np.random.randn(1000))
                sig1.create_dataset("waveform", data=np.random.randn(1000))
                
                # Signal 2: Invalid 8-bit (too many levels)
                sig2 = group.create_group("signal_002")
                data = sig2.create_dataset("quantized", data=np.random.choice(np.linspace(-1, 1, 300), 1000))
                data.attrs['bit_depth'] = 8
                data.attrs['target_snr'] = 20.0
                sig2.create_dataset("noise", data=np.random.randn(1000))
                sig2.create_dataset("waveform", data=np.random.randn(1000))
                
                # Signal 3: Valid 16-bit
                sig3 = group.create_group("signal_003")
                data = sig3.create_dataset("quantized", data=np.random.choice(np.linspace(-1, 1, 65536), 1000))
                data.attrs['bit_depth'] = 16
                data.attrs['target_snr'] = 30.0
                sig3.create_dataset("noise", data=np.random.randn(1000))
                sig3.create_dataset("waveform", data=np.random.randn(1000))
                
            return path

    def test_validation_passes_and_fails(self, sample_dataset):
        results = validate_dataset(sample_dataset)
        
        assert results["total_signals"] == 3
        # Signal 001: Valid levels, Valid SNR (approx)
        # Signal 002: Invalid levels (>256)
        # Signal 003: Valid levels (65536 <= 65536), Valid SNR
        
        # Check level failures
        level_failures = [f for f in results["failed_signals"] if f["check"] == "level_count"]
        assert len(level_failures) == 1
        assert level_failures[0]["id"] == "signal_002"
        
        # Check summary
        assert results["summary"]["failed"] >= 1
        
        # Cleanup
        sample_dataset.unlink()

    def test_specific_bit_depth_filter(self, sample_dataset):
        # Only validate 8-bit signals
        results = validate_dataset(sample_dataset, bit_depths=[8])
        assert results["total_signals"] == 2
        assert results["summary"]["failed"] >= 1
        
        sample_dataset.unlink()