import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path
import sys

from src.analysis.layer_metrics import (
    load_activation_time_series,
    load_control_run_comparison,
    load_meg_psd,
    compute_frequency_stability,
    compute_layer_metrics,
    save_layer_metrics
)
from src.analysis.spectral import compute_welch_psd


class TestFrequencyStability:
    def test_frequency_stability_with_sinusoid(self):
        """Test frequency stability with a clear sinusoidal signal"""
        # Create a 40Hz sinusoid
        sample_rate = 100.0
        duration = 2.0  # seconds
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples)
        signal = np.sin(2 * np.pi * 40 * t)
        
        stability = compute_frequency_stability(signal, sample_rate)
        
        # Should be relatively stable (low coefficient of variation)
        assert not np.isnan(stability)
        assert stability < 0.5  # Reasonable threshold for stable signal
    
    def test_frequency_stability_with_noise(self):
        """Test frequency stability with noisy signal"""
        sample_rate = 100.0
        duration = 2.0
        n_samples = int(sample_rate * duration)
        noise = np.random.randn(n_samples)
        
        stability = compute_frequency_stability(noise, sample_rate)
        
        # Should be less stable (higher coefficient of variation)
        assert not np.isnan(stability)
    
    def test_frequency_stability_with_short_signal(self):
        """Test frequency stability with very short signal"""
        short_signal = np.random.randn(5)
        
        stability = compute_frequency_stability(short_signal, 100.0)
        
        # Should return NaN for very short signals
        assert np.isnan(stability)


class TestLayerMetricsComputation:
    def test_compute_layer_metrics_basic(self):
        """Test basic layer metrics computation"""
        # Create mock activation data
        activation_data = {
            0: {0: np.random.randn(1000), 1: np.random.randn(1000)},
            1: {0: np.random.randn(1000), 1: np.random.randn(1000)}
        }
        
        # Create mock MEG PSD
        meg_psd = np.random.randn(1, 500)
        
        metrics_df = compute_layer_metrics(activation_data, meg_psd, sample_rate=100.0)
        
        # Check DataFrame structure
        assert 'layer_id' in metrics_df.columns
        assert 'head_id' in metrics_df.columns
        assert 'frequency_stability' in metrics_df.columns
        assert 'sdc_metric' in metrics_df.columns
        
        # Check number of rows
        assert len(metrics_df) == 4  # 2 layers * 2 heads
        
        # Check that values are not all NaN
        assert not metrics_df['frequency_stability'].isna().all()
    
    def test_compute_layer_metrics_with_sinusoidal_signal(self):
        """Test metrics computation with sinusoidal signal"""
        sample_rate = 100.0
        duration = 2.0
        n_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, n_samples)
        
        # Create 40Hz sinusoidal activation
        activation_data = {
            0: {0: np.sin(2 * np.pi * 40 * t)}
        }
        
        # Create mock MEG PSD
        meg_psd = np.random.randn(1, 500)
        
        metrics_df = compute_layer_metrics(activation_data, meg_psd, sample_rate=sample_rate)
        
        # Check that we got results
        assert len(metrics_df) == 1
        assert not metrics_df['frequency_stability'].isna().all()


class TestSaveLayerMetrics:
    def test_save_layer_metrics_to_csv(self):
        """Test saving layer metrics to CSV"""
        # Create mock DataFrame
        df = pd.DataFrame({
            'layer_id': [0, 1],
            'head_id': [0, 1],
            'frequency_stability': [0.1, 0.2],
            'sdc_metric': [0.5, 0.6]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test_metrics.csv')
            save_layer_metrics(df, filepath)
            
            # Check file exists
            assert os.path.exists(filepath)
            
            # Check content
            loaded_df = pd.read_csv(filepath)
            assert len(loaded_df) == 2
            assert 'layer_id' in loaded_df.columns
            assert 'head_id' in loaded_df.columns
            assert 'frequency_stability' in loaded_df.columns
            assert 'sdc_metric' in loaded_df.columns


import pandas as pd
from unittest.mock import patch, MagicMock


class TestLoadFunctions:
    def test_load_activation_time_series_json(self):
        """Test loading activation time series from JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test_activations.json')
            
            # Create test data
            test_data = {
                0: {0: [1.0, 2.0, 3.0], 1: [4.0, 5.0, 6.0]},
                1: {0: [7.0, 8.0, 9.0]}
            }
            
            with open(filepath, 'w') as f:
                json.dump(test_data, f)
            
            loaded = load_activation_time_series(filepath)
            
            assert 0 in loaded
            assert 0 in loaded[0]
            assert isinstance(loaded[0][0], np.ndarray)
            assert len(loaded[0][0]) == 3
    
    def test_load_control_run_comparison(self):
        """Test loading control run comparison"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test_comparison.json')
            
            test_data = {
                "oscillatory_coherence": 0.8,
                "baseline_coherence": 0.5,
                "coherence_difference": 0.3
            }
            
            with open(filepath, 'w') as f:
                json.dump(test_data, f)
            
            loaded = load_control_run_comparison(filepath)
            
            assert loaded["oscillatory_coherence"] == 0.8
            assert loaded["baseline_coherence"] == 0.5
            assert loaded["coherence_difference"] == 0.3
    
    def test_load_meg_psd(self):
        """Test loading MEG PSD"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test_meg.npy')
            
            test_data = np.random.randn(100, 500)
            np.save(filepath, test_data)
            
            loaded = load_meg_psd(filepath)
            
            assert loaded.shape == (100, 500)
            assert isinstance(loaded, np.ndarray)
    
    def test_load_meg_psd_1d(self):
        """Test loading 1D MEG PSD (should be expanded)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test_meg_1d.npy')
            
            test_data = np.random.randn(500)
            np.save(filepath, test_data)
            
            loaded = load_meg_psd(filepath)
            
            # Should be expanded to 2D
            assert loaded.shape == (1, 500)
    
    def test_load_file_not_found(self):
        """Test loading non-existent file"""
        with pytest.raises(FileNotFoundError):
            load_activation_time_series('/nonexistent/file.json')
        
        with pytest.raises(FileNotFoundError):
            load_control_run_comparison('/nonexistent/file.json')
        
        with pytest.raises(FileNotFoundError):
            load_meg_psd('/nonexistent/file.npy')