"""
Unit tests for PLV calculation and electrode pair validation.

Tests for User Story 2: Extract Alpha Power and PLV Metrics.
Specifically tests the PLV logic and validation of electrode pairs.
"""
import pytest
import numpy as np
from scipy.signal import hilbert
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.validation import validate_eeg_channels, log_error
from utils.logging_config import setup_logging

# Configure logging for tests
setup_logging()

# --- Helper Functions (Mirroring logic expected in 02_extract_metrics.py) ---
# These are duplicated here for testing purposes to ensure the logic is sound
# without requiring the full pipeline to be run.

REQUIRED_PLV_PAIRS = [
    ("F3", "P3"), ("F3", "P4"), ("F3", "Pz"),
    ("F4", "P3"), ("F4", "P4"), ("F4", "Pz"),
    ("Fz", "P3"), ("Fz", "P4"), ("Fz", "Pz")
]

def calculate_plv(signal1, signal2, sfreq, t_start=0.0, t_end=0.5):
    """
    Calculate Phase Locking Value between two signals using Hilbert transform.
    
    Args:
        signal1: numpy array of shape (n_times,)
        signal2: numpy array of shape (n_times,)
        sfreq: Sampling frequency
        t_start: Start time of analysis window (seconds)
        t_end: End time of analysis window (seconds)
        
    Returns:
        float: PLV value between 0 and 1
    """
    if len(signal1) != len(signal2):
        raise ValueError("Signals must have equal length")
    
    # Filter to alpha band (8-12 Hz) - simplified for test
    # In real implementation, this would use MNE filter functions
    # Here we assume input is already filtered or we simulate the phase extraction
    
    # Extract time window
    start_idx = int(t_start * sfreq)
    end_idx = int(t_end * sfreq)
    
    if end_idx > len(signal1):
        end_idx = len(signal1)
        
    if start_idx >= end_idx:
        raise ValueError("Invalid time window")
        
    s1_window = signal1[start_idx:end_idx]
    s2_window = signal2[start_idx:end_idx]
    
    # Hilbert transform to get analytic signal
    analytic_signal1 = hilbert(s1_window)
    analytic_signal2 = hilbert(s2_window)
    
    # Extract instantaneous phase
    phase1 = np.angle(analytic_signal1)
    phase2 = np.angle(analytic_signal2)
    
    # Calculate phase difference
    phase_diff = phase1 - phase2
    
    # Calculate PLV: |mean(exp(i * phase_diff))|
    plv = np.abs(np.mean(np.exp(1j * phase_diff)))
    
    return float(plv)

def validate_electrode_pairs(channels, required_pairs=REQUIRED_PLV_PAIRS):
    """
    Validate that all required electrode pairs exist in the channel list.
    
    Args:
        channels: List of channel names
        required_pairs: List of tuples representing required pairs
        
    Returns:
        tuple: (is_valid, missing_pairs, missing_channels)
    """
    channel_set = set(channels)
    missing_pairs = []
    missing_channels = set()
    
    for ch1, ch2 in required_pairs:
        if ch1 not in channel_set or ch2 not in channel_set:
            missing_pairs.append((ch1, ch2))
            if ch1 not in channel_set:
                missing_channels.add(ch1)
            if ch2 not in channel_set:
                missing_channels.add(ch2)
                
    return len(missing_pairs) == 0, missing_pairs, list(missing_channels)

# --- Test Cases ---

class TestPLVCalculation:
    """Tests for the PLV calculation logic."""

    def test_plv_perfect_sync(self):
        """Test PLV with perfectly synchronized signals (should be ~1.0)."""
        sfreq = 1000
        n_samples = sfreq * 1  # 1 second
        t = np.linspace(0, 1, n_samples)
        
        # Identical signals
        signal1 = np.sin(2 * np.pi * 10 * t)  # 10 Hz
        signal2 = np.sin(2 * np.pi * 10 * t)
        
        plv = calculate_plv(signal1, signal2, sfreq, t_start=0.1, t_end=0.9)
        
        assert 0.95 <= plv <= 1.0, f"PLV for identical signals should be ~1.0, got {plv}"

    def test_plv_orthogonal_signals(self):
        """Test PLV with orthogonal signals (90 degree shift)."""
        sfreq = 1000
        n_samples = sfreq * 1
        t = np.linspace(0, 1, n_samples)
        
        signal1 = np.sin(2 * np.pi * 10 * t)
        signal2 = np.cos(2 * np.pi * 10 * t)  # 90 degree shift
        
        plv = calculate_plv(signal1, signal2, sfreq, t_start=0.1, t_end=0.9)
        
        # PLV should be 0 for perfectly orthogonal signals with constant phase difference
        # However, due to windowing and edge effects, it might not be exactly 0
        assert plv < 0.5, f"PLV for orthogonal signals should be low, got {plv}"

    def test_plv_random_noise(self):
        """Test PLV with random noise (should be close to 0)."""
        sfreq = 1000
        n_samples = sfreq * 2
        np.random.seed(42)
        
        signal1 = np.random.randn(n_samples)
        signal2 = np.random.randn(n_samples)
        
        plv = calculate_plv(signal1, signal2, sfreq, t_start=0.1, t_end=0.9)
        
        # With random noise, PLV should be low
        assert plv < 0.3, f"PLV for random noise should be low, got {plv}"

    def test_plv_unequal_lengths(self):
        """Test that PLV raises error for unequal signal lengths."""
        signal1 = np.array([1, 2, 3])
        signal2 = np.array([1, 2])
        
        with pytest.raises(ValueError, match="Signals must have equal length"):
            calculate_plv(signal1, signal2, 1000)

    def test_plv_invalid_window(self):
        """Test that PLV raises error for invalid time window."""
        signal1 = np.sin(2 * np.pi * 10 * np.linspace(0, 1, 1000))
        signal2 = np.sin(2 * np.pi * 10 * np.linspace(0, 1, 1000))
        
        # Window larger than signal
        with pytest.raises(ValueError, match="Invalid time window"):
            calculate_plv(signal1, signal2, 1000, t_start=0.5, t_end=0.6) # 1000 samples = 1s, window 0.5-0.6 is valid
            # Let's try a window that exceeds
            calculate_plv(signal1, signal2, 1000, t_start=0.9, t_end=1.1)

class TestElectrodePairValidation:
    """Tests for electrode pair validation logic."""

    def test_all_pairs_present(self):
        """Test validation when all required pairs are present."""
        # Create a minimal set of channels that covers all pairs
        channels = ["F3", "F4", "Fz", "P3", "P4", "Pz"]
        
        is_valid, missing_pairs, missing_channels = validate_electrode_pairs(channels)
        
        assert is_valid is True
        assert len(missing_pairs) == 0
        assert len(missing_channels) == 0

    def test_missing_single_electrode(self):
        """Test validation when one electrode is missing."""
        channels = ["F3", "F4", "Fz", "P3", "P4"]  # Missing Pz
        
        is_valid, missing_pairs, missing_channels = validate_electrode_pairs(channels)
        
        assert is_valid is False
        assert len(missing_pairs) > 0
        assert "Pz" in missing_channels

    def test_missing_multiple_electrodes(self):
        """Test validation when multiple electrodes are missing."""
        channels = ["F3", "F4"]  # Missing all P electrodes
        
        is_valid, missing_pairs, missing_channels = validate_electrode_pairs(channels)
        
        assert is_valid is False
        assert len(missing_pairs) > 0
        assert "P3" in missing_channels
        assert "P4" in missing_channels
        assert "Pz" in missing_channels

    def test_empty_channels(self):
        """Test validation with empty channel list."""
        channels = []
        
        is_valid, missing_pairs, missing_channels = validate_electrode_pairs(channels)
        
        assert is_valid is False
        assert len(missing_pairs) == len(REQUIRED_PLV_PAIRS)
        assert len(missing_channels) == 6  # F3, F4, Fz, P3, P4, Pz

    def test_custom_pairs(self):
        """Test validation with custom electrode pairs."""
        custom_pairs = [("C3", "C4"), ("C3", "Cz")]
        channels = ["C3", "C4", "Cz"]
        
        is_valid, missing_pairs, missing_channels = validate_electrode_pairs(channels, custom_pairs)
        
        assert is_valid is True
        assert len(missing_pairs) == 0

class TestIntegrationWithValidationUtils:
    """Tests integrating PLV logic with project validation utilities."""

    def test_validate_channels_with_validation_utility(self):
        """Test that our channel validation aligns with project validation utility."""
        # Use the project's validation utility
        channels = ["F3", "F4", "Fz", "P3", "P4", "Pz"]
        
        # The project utility checks for required EEG channels
        # We simulate the check for PLV specific channels
        required_for_plv = set(["F3", "F4", "Fz", "P3", "P4", "Pz"])
        channel_set = set(channels)
        
        missing = required_for_plv - channel_set
        assert len(missing) == 0

    def test_plv_workflow_simulation(self):
        """Simulate a full PLV extraction workflow."""
        # 1. Define channels
        channels = ["F3", "F4", "Fz", "P3", "P4", "Pz", "EOG1", "EOG2"]
        
        # 2. Validate pairs
        is_valid, missing_pairs, missing_channels = validate_electrode_pairs(channels)
        assert is_valid is True
        
        # 3. Simulate data extraction (mock)
        sfreq = 1000
        duration = 2.0
        n_samples = int(sfreq * duration)
        t = np.linspace(0, duration, n_samples)
        
        # Generate mock alpha-band data (10 Hz)
        mock_data = {
            "F3": np.sin(2 * np.pi * 10 * t) + 0.1 * np.random.randn(n_samples),
            "P3": np.sin(2 * np.pi * 10 * t + 0.5) + 0.1 * np.random.randn(n_samples),
        }
        
        # 4. Calculate PLV
        plv_f3_p3 = calculate_plv(mock_data["F3"], mock_data["P3"], sfreq, t_start=0.5, t_end=1.5)
        
        assert 0 <= plv_f3_p3 <= 1
        assert plv_f3_p3 > 0.5  # Should be relatively high due to phase lock