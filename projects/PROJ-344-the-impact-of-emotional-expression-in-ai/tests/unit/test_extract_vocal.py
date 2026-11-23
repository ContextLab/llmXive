"""
Unit tests for vocal prosody extraction logic.
"""
import os
import sys
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.extract_vocal import (
    extract_pitch_features,
    extract_energy_features,
    extract_tempo,
    process_audio_file,
    extract_vocal_prosody
)
from code.logging_config import setup_logging

# Setup logging for tests
setup_logging()

@pytest.fixture
def dummy_audio():
    """Generate a dummy audio signal for testing."""
    sr = 22050
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    # 440 Hz sine wave
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)
    return signal, sr

def test_extract_pitch_features(dummy_audio):
    y, sr = dummy_audio
    features = extract_pitch_features(y, sr)
    
    assert isinstance(features, dict)
    assert 'pitch_mean' in features
    assert 'pitch_std' in features
    assert 'pitch_range' in features
    assert 'voiced_ratio' in features
    
    # For a pure 440Hz sine wave, mean should be close to 440
    assert 400 < features['pitch_mean'] < 480

def test_extract_energy_features(dummy_audio):
    y, sr = dummy_audio
    features = extract_energy_features(y, sr)
    
    assert isinstance(features, dict)
    assert 'energy_mean' in features
    assert 'energy_std' in features
    assert 'energy_max' in features
    assert 'energy_entropy' in features
    
    assert features['energy_mean'] > 0
    assert features['energy_max'] > 0

def test_extract_tempo(dummy_audio):
    y, sr = dummy_audio
    features = extract_tempo(y, sr)
    
    assert isinstance(features, dict)
    assert 'tempo_bpm' in features
    assert 'onset_mean' in features
    assert 'onset_std' in features
    
    # Tempo might be 0 for a pure sine wave, but keys must exist
    assert isinstance(features['tempo_bpm'], float)

def test_process_audio_file_empty(tmp_path, dummy_audio):
    # Create a dummy audio file
    import librosa
    file_path = tmp_path / "test_audio.wav"
    librosa.output.write_wav(str(file_path), dummy_audio[0], dummy_audio[1])
    
    features = process_audio_file(str(file_path), "test_id_1")
    
    assert features is not None
    assert features['interaction_id'] == "test_id_1"
    assert features['duration_sec'] > 0

def test_process_audio_file_corrupted(tmp_path):
    # Create a corrupted file (empty or invalid header)
    file_path = tmp_path / "corrupted.wav"
    file_path.write_bytes(b"NOT_A_WAVE_FILE")
    
    features = process_audio_file(str(file_path), "test_id_2")
    
    # Should return None or handle gracefully
    assert features is None

def test_extract_vocal_prosody_no_files(tmp_path):
    # Test with empty directory
    output_path = tmp_path / "features.csv"
    result = extract_vocal_prosody(str(tmp_path), str(output_path))
    
    assert result == []
    assert not os.path.exists(output_path)