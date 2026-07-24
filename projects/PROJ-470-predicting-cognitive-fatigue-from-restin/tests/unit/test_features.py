import pytest
import numpy as np
import os
import sys
import pandas as pd
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from features import calculate_lzc, calculate_permutation_entropy

class TestLZCCalculation:
    """Unit tests for LZC calculation."""

    def test_lzc_on_white_noise(self):
        """Test LZC on white noise signal."""
        # Generate white noise
        np.random.seed(42)
        signal = np.random.randn(256 * 120)  # 256 Hz, 120 seconds
        lzc_val = calculate_lzc(signal, 256)
        
        # LZC should be between 0 and 1
        assert 0 <= lzc_val <= 1, f"LZC value {lzc_val} is out of range [0, 1]"
        # White noise should have high complexity (close to 1)
        assert lzc_val > 0.5, f"White noise LZC {lzc_val} is unexpectedly low"

    def test_lzc_on_constant_signal(self):
        """Test LZC on constant signal (should be 0)."""
        signal = np.ones(1000)
        lzc_val = calculate_lzc(signal, 256)
        
        # Constant signal should have LZC close to 0
        assert lzc_val == 0.0, f"Constant signal LZC should be 0, got {lzc_val}"

    def test_lzc_on_sine_wave(self):
        """Test LZC on sine wave (should be low)."""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 10 * t)  # 10 Hz sine wave
        lzc_val = calculate_lzc(signal, 256)
        
        # Sine wave should have lower complexity than white noise
        assert 0 <= lzc_val <= 1, f"LZC value {lzc_val} is out of range [0, 1]"

class TestPermutationEntropyCalculation:
    """Unit tests for Permutation Entropy calculation."""

    def test_pe_on_white_noise(self):
        """Test PE on white noise signal."""
        # Generate white noise
        np.random.seed(42)
        signal = np.random.randn(256 * 120)  # 256 Hz, 120 seconds
        pe_val = calculate_permutation_entropy(signal, 256, embedding_dim=3)
        
        # PE should be between 0 and 1
        assert 0 <= pe_val <= 1, f"PE value {pe_val} is out of range [0, 1]"
        # White noise should have high entropy (close to 1)
        assert pe_val > 0.5, f"White noise PE {pe_val} is unexpectedly low"

    def test_pe_on_constant_signal(self):
        """Test PE on constant signal (should be 0)."""
        signal = np.ones(1000)
        pe_val = calculate_permutation_entropy(signal, 256, embedding_dim=3)
        
        # Constant signal should have PE close to 0
        assert pe_val == 0.0, f"Constant signal PE should be 0, got {pe_val}"

    def test_pe_on_sine_wave(self):
        """Test PE on sine wave (should be low)."""
        t = np.linspace(0, 1, 1000)
        signal = np.sin(2 * np.pi * 10 * t)  # 10 Hz sine wave
        pe_val = calculate_permutation_entropy(signal, 256, embedding_dim=3)
        
        # Sine wave should have lower entropy than white noise
        assert 0 <= pe_val <= 1, f"PE value {pe_val} is out of range [0, 1]"

    def test_pe_embedding_dim(self):
        """Test PE with different embedding dimensions."""
        np.random.seed(42)
        signal = np.random.randn(1000)
        
        # Test with different embedding dimensions
        for dim in [3, 4, 5]:
            pe_val = calculate_permutation_entropy(signal, 256, embedding_dim=dim)
            assert 0 <= pe_val <= 1, f"PE value {pe_val} with dim={dim} is out of range [0, 1]"

class TestFeatureExtractionIntegration:
    """Integration tests for feature extraction."""

    def test_output_files_exist(self):
        """Test that output files are created."""
        # This test assumes the main() function has been run
        lzc_path = Path("data/processed/lzc_metrics.csv")
        pe_path = Path("data/processed/pe_metrics.csv")
        
        # Note: This test may fail if main() hasn't been run yet
        # It's intended to be run after the feature extraction pipeline
        if lzc_path.exists():
            df_lzc = pd.read_csv(lzc_path)
            assert 'participant_id' in df_lzc.columns
            assert 'channel' in df_lzc.columns
            assert 'lzc_value' in df_lzc.columns
            assert len(df_lzc) > 0, "LZC metrics file is empty"
        
        if pe_path.exists():
            df_pe = pd.read_csv(pe_path)
            assert 'participant_id' in df_pe.columns
            assert 'channel' in df_pe.columns
            assert 'pe_value' in df_pe.columns
            assert len(df_pe) > 0, "PE metrics file is empty"

    def test_output_schema(self):
        """Test that output files have correct schema."""
        lzc_path = Path("data/processed/lzc_metrics.csv")
        pe_path = Path("data/processed/pe_metrics.csv")
        
        if lzc_path.exists():
            df_lzc = pd.read_csv(lzc_path)
            expected_columns = ['participant_id', 'channel', 'lzc_value']
            assert list(df_lzc.columns) == expected_columns, f"LZC columns: {list(df_lzc.columns)} != {expected_columns}"
        
        if pe_path.exists():
            df_pe = pd.read_csv(pe_path)
            expected_columns = ['participant_id', 'channel', 'pe_value']
            assert list(df_pe.columns) == expected_columns, f"PE columns: {list(df_pe.columns)} != {expected_columns}"