import pytest
import numpy as np
import pandas as pd
import os
import tempfile
from pathlib import Path

from stats import (
    detect_non_stationary_segments,
    handle_non_stationary_segments,
    StatsError
)

class TestChirpHandling:
    """Tests for non-stationary (chirp) signal handling."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create sample driving data with a known chirp segment
        self.timestamps = np.linspace(0, 10, 1000)
        # Create a signal with a linear frequency sweep (chirp)
        # f(t) = 1 + 0.5*t (frequency increases from 1 to 6 Hz)
        t = self.timestamps
        phase = 2 * np.pi * (1 * t + 0.25 * t**2)
        self.signal = np.sin(phase)
        
        self.driving_data = pd.DataFrame({
            'timestamp': self.timestamps,
            'amplitude': self.signal
        })

    def test_detect_chirp_segments(self):
        """Test that chirp segments are correctly detected."""
        result = detect_non_stationary_segments(self.driving_data, threshold=0.1)
        
        assert 'is_chirp' in result.columns
        assert len(result) == len(self.driving_data)
        
        # At least some segments should be detected as chirp
        # (the frequency is changing, so derivative should exceed threshold)
        assert result['is_chirp'].sum() > 0, "Expected some chirp segments to be detected"

    def test_handle_non_stationary_exclude(self):
        """Test exclusion strategy for non-stationary segments."""
        chirp_result = detect_non_stationary_segments(self.driving_data, threshold=0.1)
        
        # Create sample energy data
        energy_data = pd.DataFrame({
            'timestamp': self.timestamps,
            'E_trans': np.random.rand(1000) * 10,
            'E_rot': np.random.rand(1000) * 5,
            'particle_id': np.repeat(np.arange(10), 100)
        })
        
        result = handle_non_stationary_segments(
            energy_data, 
            chirp_result, 
            strategy='exclude'
        )
        
        assert 'chirp_strategy' in result.columns
        assert 'chirp_value' in result.columns
        assert result['chirp_strategy'].unique() == ['excluded']
        
        # Check that chirp_value matches the is_chirp flag
        merged = pd.merge(
            result,
            chirp_result[['timestamp', 'is_chirp']],
            on='timestamp',
            how='left'
        )
        assert np.array_equal(
            result['chirp_value'].values,
            merged['is_chirp'].astype(int).values
        )

    def test_handle_non_stationary_bin(self):
        """Test binning strategy for non-stationary segments."""
        chirp_result = detect_non_stationary_segments(self.driving_data, threshold=0.1)
        
        energy_data = pd.DataFrame({
            'timestamp': self.timestamps,
            'E_trans': np.random.rand(1000) * 10
        })
        
        result = handle_non_stationary_segments(
            energy_data,
            chirp_result,
            strategy='bin'
        )
        
        assert 'chirp_strategy' in result.columns
        assert 'chirp_value' in result.columns
        assert result['chirp_strategy'].unique() == ['binned']

    def test_invalid_strategy(self):
        """Test that invalid strategy raises error."""
        chirp_result = detect_non_stationary_segments(self.driving_data, threshold=0.1)
        
        energy_data = pd.DataFrame({
            'timestamp': self.timestamps,
            'E_trans': np.random.rand(1000) * 10
        })
        
        with pytest.raises(StatsError, match="Unknown strategy"):
            handle_non_stationary_segments(
                energy_data,
                chirp_result,
                strategy='invalid'
            )

    def test_insufficient_data_points(self):
        """Test handling of insufficient data points."""
        # Create data with only 1 point
        driving_data = pd.DataFrame({
            'timestamp': [0.0],
            'amplitude': [1.0]
        })
        
        result = detect_non_stationary_segments(driving_data, threshold=0.1)
        
        # Should return data unchanged with warning
        assert 'is_chirp' in result.columns
        assert result['is_chirp'].sum() == 0

    def test_zero_time_step(self):
        """Test handling of zero time step."""
        driving_data = pd.DataFrame({
            'timestamp': [0.0, 0.0, 0.0],
            'amplitude': [1.0, 2.0, 3.0]
        })
        
        with pytest.raises(StatsError, match="Time step cannot be zero"):
            detect_non_stationary_segments(driving_data, threshold=0.1)

    def test_bin_energy_data_with_chirp(self, tmp_path):
        """Test bin_energy_data with chirp handling."""
        # Create temporary energy file
        energy_file = tmp_path / "energy_samples.csv"
        energy_data = pd.DataFrame({
            'timestamp': self.timestamps,
            'E_trans': np.random.rand(1000) * 10,
            'particle_id': np.repeat(np.arange(10), 100)
        })
        energy_data.to_csv(energy_file, index=False)
        
        # Create chirp handling result file
        chirp_result = detect_non_stationary_segments(self.driving_data, threshold=0.1)
        chirp_file = tmp_path / "chirp_handling_result.csv"
        chirp_result.to_csv(chirp_file, index=False)
        
        from stats import bin_energy_data
        
        result = bin_energy_data(
            str(energy_file),
            chirp_file=str(chirp_file)
        )
        
        assert len(result) <= len(energy_data)  # Some may be excluded
        assert 'timestamp' in result.columns

    def test_bin_energy_data_rejects_test_prefix(self, tmp_path):
        """Test that bin_energy_data rejects files with test_ prefix."""
        energy_file = tmp_path / "test_energy_samples.csv"
        energy_data = pd.DataFrame({
            'timestamp': self.timestamps,
            'E_trans': np.random.rand(1000) * 10
        })
        energy_data.to_csv(energy_file, index=False)
        
        from stats import bin_energy_data
        
        with pytest.raises(StatsError, match="Rejecting file with test_ prefix"):
            bin_energy_data(str(energy_file))

    def test_bin_energy_data_missing_file(self, tmp_path):
        """Test handling of missing energy file."""
        from stats import bin_energy_data
        
        with pytest.raises(StatsError, match="Energy file not found"):
            bin_energy_data(str(tmp_path / "nonexistent.csv"))

    def test_chirp_handling_result_schema(self, tmp_path):
        """Test that chirp handling result has correct schema."""
        # Create driving data
        driving_file = tmp_path / "driving_signals.csv"
        self.driving_data.to_csv(driving_file, index=False)
        
        # Detect chirp
        chirp_result = detect_non_stationary_segments(self.driving_data, threshold=0.1)
        
        # Create unified result file as per T029 requirement
        unified_result = pd.DataFrame({
            'timestamp': self.timestamps,
            'strategy': ['excluded' if is_chirp else 'binned' for is_chirp in chirp_result['is_chirp']],
            'value': chirp_result['is_chirp'].astype(int)
        })
        
        result_file = tmp_path / "chirp_handling_result.csv"
        unified_result.to_csv(result_file, index=False)
        
        # Verify schema
        loaded = pd.read_csv(result_file)
        assert 'timestamp' in loaded.columns
        assert 'strategy' in loaded.columns
        assert 'value' in loaded.columns
        
        # Check valid strategies
        assert set(loaded['strategy'].unique()).issubset({'excluded', 'binned'})
        assert loaded['value'].dtype in [np.int64, np.int32, int]
        assert set(loaded['value'].unique()).issubset({0, 1})