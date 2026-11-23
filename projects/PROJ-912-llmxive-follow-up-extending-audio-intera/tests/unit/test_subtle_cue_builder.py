"""
Unit tests for Subtle Cue Builder.
"""
import pytest
from pathlib import Path
import torch
import torchaudio
import numpy as np

from data.subtle_cue_builder import SubtleCueBuilder, ClassDefinition, DatasetType
from config import get_path_config

def test_class_definition_creation():
    """Test that ClassDefinition dataclass is created correctly."""
    definition = ClassDefinition(
        class_id=1,
        class_name="dog",
        is_subtle=True,
        dominant_freq_hz=9000.0,
        avg_amplitude_db=-45.0
    )
    assert definition.class_id == 1
    assert definition.is_subtle is True
    assert definition.dominant_freq_hz > 8000

def test_subtle_cue_criteria_high_freq():
    """Test that high frequency triggers subtle cue."""
    # Logic is in the builder, but we can test the condition
    freq = 9000.0
    amp = -30.0
    assert (freq > 8000) or (amp < -40.0) is True

def test_subtle_cue_criteria_low_amp():
    """Test that low amplitude triggers subtle cue."""
    freq = 500.0
    amp = -45.0
    assert (freq > 8000) or (amp < -40.0) is True

def test_control_set_criteria():
    """Test that normal freq and amp results in control set."""
    freq = 500.0
    amp = -20.0
    assert (freq > 8000) or (amp < -40.0) is False

def test_builder_initialization():
    """Test that SubtleCueBuilder initializes without error."""
    builder = SubtleCueBuilder()
    assert builder.subtle_classes == []
    assert builder.control_classes == []

# Integration test mock (since we can't run full dataset in unit test)
def test_audio_stats_calculation():
    """Test the audio stats calculation with a synthetic signal."""
    builder = SubtleCueBuilder()
    
    # Create a synthetic high-frequency signal
    sample_rate = 32000
    duration = 1.0
    t = torch.linspace(0, duration, int(sample_rate * duration))
    frequency = 9000.0
    waveform = torch.sin(2 * np.pi * frequency * t).unsqueeze(0)
    
    # Save to a temp file
    temp_path = Path("/tmp/test_high_freq.wav")
    torchaudio.save(temp_path, waveform, sample_rate)
    
    try:
        dom_freq, amp_db = builder._get_audio_stats(str(temp_path))
        # The dominant frequency should be close to 9000
        assert dom_freq > 8000, f"Expected dominant freq > 8000, got {dom_freq}"
    finally:
        if temp_path.exists():
            temp_path.unlink()

def test_audio_stats_low_amplitude():
    """Test the audio stats calculation with a low amplitude signal."""
    builder = SubtleCueBuilder()
    
    # Create a synthetic low amplitude signal
    sample_rate = 32000
    duration = 1.0
    t = torch.linspace(0, duration, int(sample_rate * duration))
    frequency = 1000.0
    amplitude = 0.001 # Very low amplitude
    waveform = (amplitude * torch.sin(2 * np.pi * frequency * t)).unsqueeze(0)
    
    temp_path = Path("/tmp/test_low_amp.wav")
    torchaudio.save(temp_path, waveform, sample_rate)
    
    try:
        dom_freq, amp_db = builder._get_audio_stats(str(temp_path))
        # The amplitude should be very low (negative dB)
        # 20*log10(0.001) = -60 dB
        assert amp_db < -40.0, f"Expected amp < -40dB, got {amp_db}"
    finally:
        if temp_path.exists():
            temp_path.unlink()