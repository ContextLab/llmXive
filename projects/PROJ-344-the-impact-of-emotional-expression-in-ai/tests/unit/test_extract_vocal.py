"""
Unit tests for vocal prosody extraction (T014).
Tests pitch, energy, and tempo extraction logic using synthetic audio.
"""

import os
import sys
import numpy as np
import pytest
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.extract_vocal import (
    extract_pitch_features,
    extract_energy_features,
    extract_tempo,
    process_audio_file,
    SAMPLE_RATE,
    HOP_LENGTH
)
from code.logging_config import setup_logging

# Setup logging for tests
setup_logging()

class TestPitchFeatures:
    def test_extract_pitch_sine_wave(self):
        """Test pitch extraction on a known sine wave (440 Hz)."""
        duration = 1.0  # seconds
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        frequency = 440.0
        y = np.sin(2 * np.pi * frequency * t)

        stats = extract_pitch_features(y, SAMPLE_RATE)

        # Should detect a mean pitch close to 440 Hz
        assert 400 < stats["mean_pitch"] < 480, f"Expected ~440Hz, got {stats['mean_pitch']}"
        assert stats["std_pitch"] >= 0

    def test_extract_pitch_silence(self):
        """Test pitch extraction on silence (should return 0 or very low)."""
        y = np.zeros(int(SAMPLE_RATE * 1.0))
        stats = extract_pitch_features(y, SAMPLE_RATE)

        # No valid pitch should be detected
        assert stats["mean_pitch"] == 0.0 or stats["std_pitch"] == 0.0

class TestEnergyFeatures:
    def test_extract_energy_constant_signal(self):
        """Test energy extraction on a constant amplitude signal."""
        duration = 1.0
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        amplitude = 0.5
        y = amplitude * np.sin(2 * np.pi * 440 * t)

        stats = extract_energy_features(y)

        # RMS should be positive and less than 1.0 for normalized signal
        assert stats["mean_energy"] > 0
        assert stats["mean_energy"] < 1.0
        assert stats["std_energy"] >= 0

    def test_extract_energy_silence(self):
        """Test energy extraction on silence."""
        y = np.zeros(int(SAMPLE_RATE * 1.0))
        stats = extract_energy_features(y)

        # Energy should be near zero
        assert stats["mean_energy"] == pytest.approx(0.0, abs=1e-6)

class TestTempo:
    def test_extract_tempo_rhythmic_signal(self):
        """Test tempo extraction on a rhythmic signal."""
        # Create a simple beat pattern (clicks every 0.5s -> 120 BPM)
        duration = 2.0
        sr = SAMPLE_RATE
        y = np.zeros(int(sr * duration))
        # Place clicks at 0.0, 0.5, 1.0, 1.5 seconds
        for i in range(0, int(sr * duration), int(sr * 0.5)):
            if i < len(y):
                y[i] = 1.0

        tempo = extract_tempo(y, sr)

        # Should detect around 120 BPM (with some tolerance)
        assert 100 < tempo < 140, f"Expected ~120 BPM, got {tempo}"

class TestProcessAudioFile:
    def test_process_nonexistent_file(self):
        """Test that processing a non-existent file returns None."""
        result = process_audio_file(Path("/nonexistent/file.wav"))
        assert result is None

    def test_process_empty_file(self, tmp_path):
        """Test processing an empty audio file."""
        empty_file = tmp_path / "empty.wav"
        # Create a minimal WAV file header (invalid but file exists)
        empty_file.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")

        result = process_audio_file(empty_file)
        # Should handle gracefully (return None or empty dict)
        assert result is None or result.get("mean_pitch") == 0.0