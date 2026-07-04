"""
Unit tests for vocal prosody extraction (T014)

Tests pitch, energy, and tempo extraction logic.
Uses mocked audio data to ensure deterministic behavior.
"""
import os
import sys
import tempfile
import json
import numpy as np
import pandas as pd
import librosa
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.extract_vocal import (
    extract_pitch_features,
    extract_energy_features,
    extract_tempo_features,
    process_audio_file,
    load_audio_manifest,
    save_features,
    main
)

@pytest.fixture
def mock_audio():
    """Generate a simple mock audio signal."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    # Simple sine wave at 440Hz (A4)
    y = 0.5 * np.sin(2 * np.pi * 440 * t)
    return y, sr

@pytest.fixture
def temp_audio_file(mock_audio):
    """Create a temporary WAV file with mock audio."""
    y, sr = mock_audio
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
        librosa.output.write_wav(temp_path, y, sr)
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_manifest(temp_audio_file):
    """Create a temporary manifest file."""
    manifest_data = [
        {"interaction_id": "test_001", "audio_path": temp_audio_file}
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(manifest_data, f)
        manifest_path = f.name
    yield manifest_path
    os.unlink(manifest_path)

def test_extract_pitch_features(mock_audio):
    """Test pitch extraction returns expected shapes."""
    y, sr = mock_audio
    f0, voiced = extract_pitch_features(y, sr)
    
    assert isinstance(f0, np.ndarray)
    assert isinstance(voiced, np.ndarray)
    assert f0.shape == voiced.shape
    assert len(f0) > 0
    
    # For a 440Hz sine wave, mean pitch should be close to 440
    # (allowing for some algorithmic variance)
    mean_pitch = np.mean(f0[f0 > 0])
    assert 400 < mean_pitch < 480, f"Expected pitch ~440, got {mean_pitch}"

def test_extract_energy_features(mock_audio):
    """Test energy extraction returns positive values."""
    y, sr = mock_audio
    energy = extract_energy_features(y, sr)
    
    assert isinstance(energy, np.ndarray)
    assert len(energy) > 0
    assert np.all(energy >= 0)
    
    # Energy should have some variance for a sine wave
    assert np.std(energy) > 0

def test_extract_tempo_features(mock_audio):
    """Test tempo extraction returns a float."""
    y, sr = mock_audio
    # Note: Tempo estimation on a pure sine wave is unreliable,
    # but the function should return a valid float without crashing.
    tempo = extract_tempo_features(y, sr)
    
    assert isinstance(tempo, float)
    assert tempo >= 0

def test_process_audio_file(temp_audio_file):
    """Test full processing of a single audio file."""
    result = process_audio_file(temp_audio_file, "test_001")
    
    assert result is not None
    assert result["interaction_id"] == "test_001"
    assert "pitch_mean" in result
    assert "energy_mean" in result
    assert "tempo_bpm" in result
    assert "f0_series" in result
    assert "energy_series" in result
    
    # Check that series are lists
    assert isinstance(result["f0_series"], list)
    assert isinstance(result["energy_series"], list)

def test_process_corrupted_file():
    """Test handling of a non-existent file."""
    result = process_audio_file("non_existent_file.wav", "test_bad")
    assert result is None

def test_load_audio_manifest(temp_manifest, temp_audio_file):
    """Test loading audio manifest."""
    items = load_audio_manifest(temp_manifest)
    
    assert len(items) == 1
    assert items[0]["interaction_id"] == "test_001"
    assert items[0]["audio_path"] == temp_audio_file

def test_save_features(tmp_path):
    """Test saving features to CSV."""
    features = [
        {
            "interaction_id": "1",
            "pitch_mean": 200.0,
            "energy_mean": 0.5,
            "tempo_bpm": 120.0,
            "f0_series": [1, 2, 3],
            "energy_series": [0.1, 0.2, 0.3]
        },
        {
            "interaction_id": "2",
            "pitch_mean": 250.0,
            "energy_mean": 0.6,
            "tempo_bpm": 130.0,
            "f0_series": [4, 5, 6],
            "energy_series": [0.4, 0.5, 0.6]
        }
    ]
    
    output_path = tmp_path / "features.csv"
    save_features(features, str(output_path))
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    
    assert len(df) == 2
    assert list(df.columns) == [
        "interaction_id", "pitch_mean", "energy_mean", "tempo_bpm", 
        "f0_series", "energy_series"
    ]
    # Verify series are stored as strings (JSON)
    assert isinstance(df.loc[0, "f0_series"], str)

def test_main_flow(temp_manifest, tmp_path):
    """Test the full main pipeline."""
    output_path = tmp_path / "output_features.csv"
    
    main(temp_manifest, str(output_path))
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 1
    assert "pitch_mean" in df.columns
