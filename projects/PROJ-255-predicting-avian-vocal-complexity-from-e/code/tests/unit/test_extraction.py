import os
import csv
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.extraction import (
    calculate_spectral_entropy,
    calculate_bandwidth,
    count_syllables,
    extract_vocal_metrics,
    extract_metrics_from_dataset
)

@pytest.fixture
def sample_audio_data():
    """Create sample audio data for testing."""
    # Generate a simple sine wave with some noise
    sr = 22050
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    frequency = 440  # A4 note
    y = np.sin(2 * np.pi * frequency * t) + 0.1 * np.random.randn(len(t))
    return y, sr

@pytest.fixture
def temp_audio_file(sample_audio_data):
    """Create a temporary audio file for testing."""
    import librosa
    
    y, sr = sample_audio_data
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
        librosa.output.write_wav(temp_path, y, sr)
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestSpectralEntropy:
    def test_spectral_entropy_basic(self, sample_audio_data):
        """Test basic spectral entropy calculation."""
        y, sr = sample_audio_data
        entropy = calculate_spectral_entropy(y, sr)
        
        assert isinstance(entropy, float)
        assert entropy >= 0

    def test_spectral_entropy_empty_signal(self):
        """Test spectral entropy with empty signal."""
        y = np.array([])
        sr = 22050
        entropy = calculate_spectral_entropy(y, sr)
        
        assert entropy == 0.0

    def test_spectral_entropy_noise(self):
        """Test that noise has higher entropy than pure tone."""
        sr = 22050
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration))
        
        # Pure tone
        pure_tone = np.sin(2 * np.pi * 440 * t)
        
        # Noise
        noise = np.random.randn(len(t))
        
        entropy_tone = calculate_spectral_entropy(pure_tone, sr)
        entropy_noise = calculate_spectral_entropy(noise, sr)
        
        # Noise should generally have higher entropy
        assert entropy_noise >= entropy_tone - 0.1  # Allow small tolerance

class TestBandwidth:
    def test_bandwidth_basic(self, sample_audio_data):
        """Test basic bandwidth calculation."""
        y, sr = sample_audio_data
        bandwidth = calculate_bandwidth(y, sr)
        
        assert isinstance(bandwidth, float)
        assert bandwidth >= 0

    def test_bandwidth_empty_signal(self):
        """Test bandwidth with empty signal."""
        y = np.array([])
        sr = 22050
        bandwidth = calculate_bandwidth(y, sr)
        
        assert bandwidth == 0.0

    def test_bandwidth_range(self, sample_audio_data):
        """Test that bandwidth is within reasonable range."""
        y, sr = sample_audio_data
        bandwidth = calculate_bandwidth(y, sr)
        
        # Bandwidth should be less than Nyquist frequency
        assert bandwidth < sr / 2

class TestSyllableCount:
    def test_syllable_count_basic(self, sample_audio_data):
        """Test basic syllable count."""
        y, sr = sample_audio_data
        count = count_syllables(y, sr)
        
        assert isinstance(count, int)
        assert count >= 0

    def test_syllable_count_empty_signal(self):
        """Test syllable count with empty signal."""
        y = np.array([])
        sr = 22050
        count = count_syllables(y, sr)
        
        assert count == 0

    def test_syllable_count_thresholds(self, sample_audio_data):
        """Test syllable count with different thresholds."""
        y, sr = sample_audio_data
        
        count_default = count_syllables(y, sr)
        count_strict = count_syllables(y, sr, min_duration=0.1, min_energy=0.1)
        
        # Stricter thresholds should result in fewer or equal syllables
        assert count_strict <= count_default

class TestExtractVocalMetrics:
    def test_extract_vocal_metrics_file(self, temp_audio_file):
        """Test extraction from actual file."""
        metrics = extract_vocal_metrics(temp_audio_file)
        
        assert 'duration' in metrics
        assert 'syllable_count' in metrics
        assert 'bandwidth' in metrics
        assert 'spectral_entropy' in metrics
        
        assert metrics['duration'] > 0
        assert metrics['syllable_count'] >= 0
        assert metrics['bandwidth'] >= 0
        assert metrics['spectral_entropy'] >= 0

    def test_extract_vocal_metrics_nonexistent_file(self):
        """Test extraction from non-existent file."""
        metrics = extract_vocal_metrics('/nonexistent/path/audio.wav')
        
        assert metrics['duration'] == 0.0
        assert metrics['syllable_count'] == 0
        assert metrics['bandwidth'] == 0.0
        assert metrics['spectral_entropy'] == 0.0

class TestExtractMetricsFromDataset:
    def test_extract_metrics_from_dataset_basic(self, temp_audio_file):
        """Test extraction from dataset CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input CSV
            input_csv = os.path.join(tmpdir, 'input.csv')
            output_csv = os.path.join(tmpdir, 'output.csv')
            
            with open(input_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'filename', 'audio_path'])
                writer.writerow(['1', 'test.wav', temp_audio_file])
            
            # Run extraction
            processed, errors = extract_metrics_from_dataset(input_csv, output_csv)
            
            assert processed == 1
            assert errors == 0
            assert os.path.exists(output_csv)
            
            # Verify output CSV
            with open(output_csv, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert 'duration' in rows[0]
                assert 'syllable_count' in rows[0]
                assert 'bandwidth' in rows[0]
                assert 'spectral_entropy' in rows[0]

    def test_extract_metrics_from_dataset_multiple_files(self, temp_audio_file):
        """Test extraction from multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create input CSV with multiple entries
            input_csv = os.path.join(tmpdir, 'input.csv')
            output_csv = os.path.join(tmpdir, 'output.csv')
            
            with open(input_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'filename', 'audio_path'])
                writer.writerow(['1', 'test1.wav', temp_audio_file])
                writer.writerow(['2', 'test2.wav', temp_audio_file])
                writer.writerow(['3', 'missing.wav', '/nonexistent/path.wav'])
            
            # Run extraction
            processed, errors = extract_metrics_from_dataset(input_csv, output_csv)
            
            assert processed == 2
            assert errors == 1
            assert os.path.exists(output_csv)