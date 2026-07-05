"""
Unit tests for vocal metrics extraction module.
"""

import os
import csv
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.data.extraction import (
    calculate_spectral_entropy,
    calculate_bandwidth,
    count_syllables,
    extract_vocal_metrics,
    extract_metrics_from_dataset
)

class TestSpectralEntropy:
    def test_empty_audio_returns_zero(self):
        audio = np.array([])
        sr = 22050
        result = calculate_spectral_entropy(audio, sr)
        assert result == 0.0

    def test_silence_returns_low_entropy(self):
        audio = np.zeros(1000)
        sr = 22050
        result = calculate_spectral_entropy(audio, sr)
        # Silence should have very low entropy
        assert result >= 0.0

    def test_random_audio_has_positive_entropy(self):
        audio = np.random.randn(10000)
        sr = 22050
        result = calculate_spectral_entropy(audio, sr)
        assert result > 0.0

class TestBandwidth:
    def test_empty_audio_returns_zero(self):
        audio = np.array([])
        sr = 22050
        result = calculate_bandwidth(audio, sr)
        assert result == 0.0

    def test_silence_returns_low_bandwidth(self):
        audio = np.zeros(1000)
        sr = 22050
        result = calculate_bandwidth(audio, sr)
        assert result >= 0.0

    def test_tone_has_specific_bandwidth(self):
        sr = 22050
        t = np.linspace(0, 1, sr)
        # Pure tone at 440 Hz
        audio = np.sin(2 * np.pi * 440 * t)
        result = calculate_bandwidth(audio, sr)
        # Pure tone should have relatively low bandwidth
        assert result > 0.0

class TestSyllableCount:
    def test_empty_audio_returns_zero(self):
        audio = np.array([])
        sr = 22050
        result = count_syllables(audio, sr)
        assert result == 0

    def test_silence_returns_zero(self):
        audio = np.zeros(1000)
        sr = 22050
        result = count_syllables(audio, sr)
        assert result == 0

    def test_impulse_detects_onset(self):
        sr = 22050
        audio = np.zeros(1000)
        audio[500] = 1.0  # Single impulse
        result = count_syllables(audio, sr)
        # Should detect at least one onset
        assert result >= 1

class TestExtractVocalMetrics:
    def test_empty_file_returns_zeros(self):
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        
        try:
            # Create empty file
            with open(temp_path, 'wb') as f:
                pass
            
            result = extract_vocal_metrics(temp_path)
            
            assert result['duration'] == 0.0
            assert result['syllable_count'] == 0
            assert result['bandwidth_hz'] == 0.0
            assert result['spectral_entropy'] == 0.0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_nonexistent_file_returns_zeros(self):
        result = extract_vocal_metrics('/nonexistent/path/file.wav')
        
        assert result['duration'] == 0.0
        assert result['syllable_count'] == 0
        assert result['bandwidth_hz'] == 0.0
        assert result['spectral_entropy'] == 0.0

class TestExtractMetricsFromDataset:
    def test_empty_input_returns_zeros(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('audio_path,species_id\n')
            temp_path = f.name
        
        output_path = temp_path + '_out.csv'
        
        try:
            successful, failed = extract_metrics_from_dataset(temp_path, output_path)
            
            assert successful == 0
            assert failed == 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_valid_csv_processing(self):
        # Create a temporary CSV with valid structure
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['audio_path', 'species_id', 'location_id'])
            writer.writerow(['/nonexistent/audio1.wav', 'species_1', 'loc_1'])
            writer.writerow(['/nonexistent/audio2.wav', 'species_2', 'loc_2'])
            temp_input = f.name
        
        output_path = temp_input + '_out.csv'
        
        try:
            successful, failed = extract_metrics_from_dataset(temp_input, output_path)
            
            # Both should fail due to non-existent files
            assert successful == 0
            assert failed == 2
            
            # Check output file exists and has correct structure
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert 'duration' in rows[0]
                assert 'syllable_count' in rows[0]
                assert 'bandwidth_hz' in rows[0]
                assert 'spectral_entropy' in rows[0]
        finally:
            if os.path.exists(temp_input):
                os.unlink(temp_input)
            if os.path.exists(output_path):
                os.unlink(output_path)