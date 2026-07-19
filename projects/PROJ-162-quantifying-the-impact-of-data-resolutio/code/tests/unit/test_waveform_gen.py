"""
Unit tests for waveform generation module.

Tests FR-001: Verify waveform generation covers low-to-high mass
and moderate-to-high distance ranges.
"""
import pytest
import numpy as np
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.waveform_gen import (
    generate_waveform_parameters,
    generate_td_waveform,
    apply_inclination_and_polarization,
    scale_waveform,
    generate_waveforms_batch,
    DEFAULT_FS,
    MIN_MASS1, MAX_MASS1,
    MIN_MASS2, MAX_MASS2,
    MIN_DIST, MAX_DIST
)

class TestWaveformGenRange:
    """Test that waveform generation covers the specified parameter ranges."""
    
    def test_mass_ranges(self):
        """Verify that generated masses are within specified bounds."""
        parameters = generate_waveform_parameters(seed=42, n_waveforms=100)
        
        for params in parameters:
            assert MIN_MASS1 <= params['mass1'] <= MAX_MASS1, \
                f"mass1 {params['mass1']} out of range [{MIN_MASS1}, {MAX_MASS1}]"
            assert MIN_MASS2 <= params['mass2'] <= MAX_MASS2, \
                f"mass2 {params['mass2']} out of range [{MIN_MASS2}, {MAX_MASS2}]"
            assert params['mass1'] >= params['mass2'], \
                f"mass1 {params['mass1']} should be >= mass2 {params['mass2']}"
    
    def test_distance_ranges(self):
        """Verify that generated distances are within specified bounds."""
        parameters = generate_waveform_parameters(seed=42, n_waveforms=100)
        
        for params in parameters:
            assert MIN_DIST <= params['distance'] <= MAX_DIST, \
                f"distance {params['distance']} out of range [{MIN_DIST}, {MAX_DIST}]"
    
    def test_sampling_frequency(self):
        """Verify that waveforms are generated at the correct sampling frequency."""
        parameters = generate_waveform_parameters(seed=42, n_waveforms=5)
        
        for params in parameters:
            assert params['sample_rate'] == DEFAULT_FS, \
                f"sample_rate {params['sample_rate']} should be {DEFAULT_FS}"
    
    def test_non_spinning(self):
        """Verify that spins are zero (non-spinning waveforms)."""
        parameters = generate_waveform_parameters(seed=42, n_waveforms=10)
        
        for params in parameters:
            assert params['spin1z'] == 0.0, f"spin1z should be 0.0, got {params['spin1z']}"
            assert params['spin2z'] == 0.0, f"spin2z should be 0.0, got {params['spin2z']}"
    
    def test_waveform_id_generation(self):
        """Verify that unique waveform IDs are generated."""
        parameters = generate_waveform_parameters(seed=42, n_waveforms=10)
        
        ids = [params['waveform_id'] for params in parameters]
        assert len(ids) == len(set(ids)), "Waveform IDs should be unique"
        
        # Check format
        for i, wid in enumerate(ids):
            assert wid == f"waveform_{i:04d}", f"ID format incorrect: {wid}"
    
    def test_parameter_consistency(self):
        """Verify that all required parameters are present."""
        required_keys = [
            'mass1', 'mass2', 'spin1z', 'spin2z', 'distance',
            'inclination', 'phase', 'polarization', 'time_shift',
            'f_lower', 'f_final', 'approximant', 'sample_rate',
            'duration', 'waveform_id'
        ]
        
        parameters = generate_waveform_parameters(seed=42, n_waveforms=1)
        params = parameters[0]
        
        for key in required_keys:
            assert key in params, f"Missing required key: {key}"
    
    def test_reproducibility(self):
        """Verify that same seed produces same results."""
        params1 = generate_waveform_parameters(seed=123, n_waveforms=5)
        params2 = generate_waveform_parameters(seed=123, n_waveforms=5)
        
        for p1, p2 in zip(params1, params2):
            assert p1['mass1'] == p2['mass1']
            assert p1['mass2'] == p2['mass2']
            assert p1['distance'] == p2['distance']
            assert p1['inclination'] == p2['inclination']
            assert p1['phase'] == p2['phase']
    
    def test_inclination_range(self):
        """Verify that inclination angles are within valid range."""
        parameters = generate_waveform_parameters(seed=42, n_waveforms=100)
        
        for params in parameters:
            # Inclination should be between 0 and pi
            assert 0 <= params['inclination'] <= np.pi, \
                f"inclination {params['inclination']} out of range [0, pi]"
    
    def test_phase_range(self):
        """Verify that phase angles are within valid range."""
        parameters = generate_waveform_parameters(seed=42, n_waveforms=100)
        
        for params in parameters:
            # Phase should be between 0 and 2*pi
            assert 0 <= params['phase'] <= 2 * np.pi, \
                f"phase {params['phase']} out of range [0, 2*pi]"
    
    def test_polarization_range(self):
        """Verify that polarization angles are within valid range."""
        parameters = generate_waveform_parameters(seed=42, n_waveforms=100)
        
        for params in parameters:
            # Polarization should be between 0 and 2*pi
            assert 0 <= params['polarization'] <= 2 * np.pi, \
                f"polarization {params['polarization']} out of range [0, 2*pi]"

class TestWaveformGeneration:
    """Test waveform generation functionality."""
    
    @pytest.mark.skip(reason="Requires PYCBC to be installed and working")
    def test_td_waveform_generation(self):
        """Test that TD waveforms can be generated."""
        params = {
            'mass1': 30.0,
            'mass2': 20.0,
            'spin1z': 0.0,
            'spin2z': 0.0,
            'f_lower': 20.0,
            'f_final': 2048.0,
            'approximant': 'IMRPhenomD',
            'sample_rate': 4096,
            'duration': 4.0
        }
        
        time_array, h_plus, h_cross = generate_td_waveform(params)
        
        assert len(time_array) > 0
        assert len(h_plus) > 0
        assert len(h_cross) > 0
        assert len(time_array) == len(h_plus) == len(h_cross)
    
    def test_inclination_polarization_application(self):
        """Test that inclination and polarization are applied correctly."""
        h_plus = np.random.randn(1000)
        h_cross = np.random.randn(1000)
        
        h_observed = apply_inclination_and_polarization(
            h_plus, h_cross,
            inclination=np.pi/4,
            polarization=np.pi/6
        )
        
        assert len(h_observed) == len(h_plus)
        assert not np.allclose(h_observed, h_plus)  # Should be different
    
    def test_waveform_scaling(self):
        """Test that waveform scaling by distance works correctly."""
        h = np.random.randn(1000)
        distance = 100.0
        
        h_scaled = scale_waveform(h, distance, reference_distance=1.0)
        
        expected_scale = 1.0 / distance
        assert np.allclose(h_scaled, h * expected_scale)
    
    def test_batch_generation_creates_files(self):
        """Test that batch generation creates output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = generate_waveforms_batch(
                n_waveforms=3,
                seed=42,
                output_dir=tmpdir
            )
            
            assert len(files) == 3
            
            for file_path in files:
                assert os.path.exists(file_path)
                assert file_path.endswith('.h5')
                
                # Check file size is non-zero
                assert os.path.getsize(file_path) > 0
    
    def test_batch_generation_metadata(self):
        """Test that generated files contain correct metadata."""
        import h5py
        
        with tempfile.TemporaryDirectory() as tmpdir:
            files = generate_waveforms_batch(
                n_waveforms=2,
                seed=42,
                output_dir=tmpdir
            )
            
            for file_path in files:
                with h5py.File(file_path, 'r') as f:
                    # Check required datasets exist
                    assert 'time' in f
                    assert 'h_plus' in f
                    assert 'h_cross' in f
                    
                    # Check required attributes
                    assert 'mass1' in f.attrs
                    assert 'mass2' in f.attrs
                    assert 'distance' in f.attrs
                    assert 'sampling_frequency' in f.attrs
                    assert 'approximant' in f.attrs
    
    def test_custom_mass_distance_ranges(self):
        """Test that custom mass and distance ranges are respected."""
        custom_mass_range = (5.0, 15.0, 3.0, 12.0)
        custom_distance_range = (50.0, 200.0)
        
        parameters = generate_waveform_parameters(
            seed=42,
            n_waveforms=10,
            mass_range=custom_mass_range,
            distance_range=custom_distance_range
        )
        
        for params in parameters:
            assert 5.0 <= params['mass1'] <= 15.0
            assert 3.0 <= params['mass2'] <= 12.0
            assert 50.0 <= params['distance'] <= 200.0
            assert params['mass1'] >= params['mass2']