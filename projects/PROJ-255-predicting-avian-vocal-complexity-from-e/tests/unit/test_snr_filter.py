"""
Unit tests for SNR calculation and filtering logic.

This module tests the Signal-to-Noise Ratio (SNR) calculation and filtering
functions used in the avian vocal complexity pipeline.

Tests cover:
- SNR calculation from audio features
- Filtering logic based on SNR thresholds
- Edge cases (zero noise, missing data)
- Exclusion logging functionality
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import os
import sys

# Add parent directory to path for imports if running standalone
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

# Mock librosa if not available for testing environment
try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    # Create mock objects for testing without librosa
    librosa = Mock()
    librosa.feature.rms = Mock(return_value=np.array([0.1, 0.2]))
    librosa.core.stft = Mock(return_value=np.array([[0.1, 0.2], [0.3, 0.4]]))

from src.data.preprocessing import calculate_snr, filter_by_snr, generate_snr_report


class TestSNRCalculation:
    """Tests for SNR calculation functions."""
    
    def test_calculate_snr_basic(self):
        """Test basic SNR calculation with known values."""
        # Create mock audio data with known signal and noise levels
        signal_power = 1.0  # 0 dB
        noise_power = 0.1   # -10 dB
        expected_snr = 10 * np.log10(signal_power / noise_power)
        
        # Mock the librosa functions
        with patch('src.data.preprocessing.librosa') as mock_librosa:
            mock_librosa.feature.rms.return_value = np.array([np.sqrt(signal_power)])
            mock_librosa.core.stft.return_value = np.array([[np.sqrt(noise_power)]])
            
            # Create a mock audio file path
            mock_audio_path = "/fake/path/audio.wav"
            
            # Calculate SNR
            result = calculate_snr(mock_audio_path, noise_floor_db=-60)
            
            # Verify the result is close to expected
            assert result is not None
            assert isinstance(result, float)
            assert abs(result - expected_snr) < 0.1
    
    def test_calculate_snr_with_high_noise(self):
        """Test SNR calculation when noise is high (low SNR)."""
        signal_power = 0.5
        noise_power = 0.8
        expected_snr = 10 * np.log10(signal_power / noise_power)
        
        with patch('src.data.preprocessing.librosa') as mock_librosa:
            mock_librosa.feature.rms.return_value = np.array([np.sqrt(signal_power)])
            mock_librosa.core.stft.return_value = np.array([[np.sqrt(noise_power)]])
            
            mock_audio_path = "/fake/path/audio.wav"
            result = calculate_snr(mock_audio_path)
            
            assert result is not None
            assert result < 0  # Should be negative SNR
            assert abs(result - expected_snr) < 0.1
    
    def test_calculate_snr_with_zero_noise(self):
        """Test SNR calculation when noise is effectively zero (should handle gracefully)."""
        signal_power = 1.0
        noise_power = 1e-10  # Very small, but not zero
        
        with patch('src.data.preprocessing.librosa') as mock_librosa:
            mock_librosa.feature.rms.return_value = np.array([np.sqrt(signal_power)])
            mock_librosa.core.stft.return_value = np.array([[np.sqrt(noise_power)]])
            
            mock_audio_path = "/fake/path/audio.wav"
            result = calculate_snr(mock_audio_path)
            
            assert result is not None
            assert result > 20  # Should be high positive SNR
    
    def test_calculate_snr_missing_file(self):
        """Test SNR calculation with missing file returns None."""
        mock_audio_path = "/fake/path/nonexistent.wav"
        
        result = calculate_snr(mock_audio_path)
        
        assert result is None
    
    def test_calculate_snr_invalid_audio(self):
        """Test SNR calculation with invalid audio data."""
        mock_audio_path = "/fake/path/invalid.wav"
        
        with patch('src.data.preprocessing.librosa') as mock_librosa:
            mock_librosa.load.side_effect = Exception("Invalid audio file")
            
            result = calculate_snr(mock_audio_path)
            
            assert result is None


class TestSNRFiltering:
    """Tests for SNR filtering logic."""
    
    def test_filter_by_snr_basic(self):
        """Test basic filtering with SNR threshold."""
        # Create sample dataset
        data = {
            'record_id': [1, 2, 3, 4, 5],
            'snr_db': [25.0, 15.0, 8.0, 12.0, 5.0],
            'species_id': ['sp1', 'sp2', 'sp3', 'sp4', 'sp5']
        }
        df = pd.DataFrame(data)
        
        # Filter with threshold of 10 dB
        filtered_df, excluded_df = filter_by_snr(df, threshold_db=10.0)
        
        # Verify results
        assert len(filtered_df) == 3  # Records with SNR > 10
        assert len(excluded_df) == 2  # Records with SNR <= 10
        
        # Check that filtered records have SNR > 10
        assert all(filtered_df['snr_db'] > 10.0)
        
        # Check that excluded records have SNR <= 10
        assert all(excluded_df['snr_db'] <= 10.0)
        
        # Verify IDs match expected
        assert set(filtered_df['record_id'].tolist()) == {1, 2, 4}
        assert set(excluded_df['record_id'].tolist()) == {3, 5}
    
    def test_filter_by_snr_no_exclusions(self):
        """Test filtering when all records pass the threshold."""
        data = {
            'record_id': [1, 2, 3],
            'snr_db': [20.0, 15.0, 12.0],
            'species_id': ['sp1', 'sp2', 'sp3']
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded_df = filter_by_snr(df, threshold_db=10.0)
        
        assert len(filtered_df) == 3
        assert len(excluded_df) == 0
    
    def test_filter_by_snr_all_excluded(self):
        """Test filtering when all records fail the threshold."""
        data = {
            'record_id': [1, 2, 3],
            'snr_db': [5.0, 3.0, 8.0],
            'species_id': ['sp1', 'sp2', 'sp3']
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded_df = filter_by_snr(df, threshold_db=10.0)
        
        assert len(filtered_df) == 0
        assert len(excluded_df) == 3
    
    def test_filter_by_snr_empty_dataframe(self):
        """Test filtering with empty dataframe."""
        df = pd.DataFrame(columns=['record_id', 'snr_db', 'species_id'])
        
        filtered_df, excluded_df = filter_by_snr(df, threshold_db=10.0)
        
        assert len(filtered_df) == 0
        assert len(excluded_df) == 0
    
    def test_filter_by_snr_missing_snr_column(self):
        """Test filtering when SNR column is missing."""
        data = {
            'record_id': [1, 2, 3],
            'species_id': ['sp1', 'sp2', 'sp3']
        }
        df = pd.DataFrame(data)
        
        # Should raise KeyError or return empty/None
        with pytest.raises(KeyError):
            filter_by_snr(df, threshold_db=10.0)
    
    def test_filter_by_snr_with_nan_values(self):
        """Test filtering when SNR column contains NaN values."""
        data = {
            'record_id': [1, 2, 3, 4],
            'snr_db': [20.0, np.nan, 5.0, 15.0],
            'species_id': ['sp1', 'sp2', 'sp3', 'sp4']
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded_df = filter_by_snr(df, threshold_db=10.0)
        
        # NaN values should be excluded
        assert len(filtered_df) == 2  # Records 1 and 4
        assert len(excluded_df) == 2  # Records 2 (NaN) and 3 (low SNR)
        
        # Verify filtered records don't have NaN
        assert not filtered_df['snr_db'].isna().any()
    
    def test_filter_by_snr_threshold_zero(self):
        """Test filtering with zero threshold (all positive SNR should pass)."""
        data = {
            'record_id': [1, 2, 3],
            'snr_db': [5.0, -2.0, 10.0],
            'species_id': ['sp1', 'sp2', 'sp3']
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded_df = filter_by_snr(df, threshold_db=0.0)
        
        assert len(filtered_df) == 2  # Records 1 and 3
        assert len(excluded_df) == 1  # Record 2 (negative SNR)
    
    def test_filter_by_snr_threshold_very_high(self):
        """Test filtering with very high threshold (all should be excluded)."""
        data = {
            'record_id': [1, 2, 3],
            'snr_db': [20.0, 15.0, 12.0],
            'species_id': ['sp1', 'sp2', 'sp3']
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded_df = filter_by_snr(df, threshold_db=100.0)
        
        assert len(filtered_df) == 0
        assert len(excluded_df) == 3


class TestSNRReportGeneration:
    """Tests for SNR report generation."""
    
    def test_generate_snr_report_basic(self):
        """Test basic report generation."""
        # Create sample filtered and excluded data
        filtered_data = {
            'record_id': [1, 2, 3],
            'snr_db': [25.0, 18.0, 12.0],
            'species_id': ['sp1', 'sp2', 'sp3']
        }
        excluded_data = {
            'record_id': [4, 5],
            'snr_db': [8.0, 5.0],
            'species_id': ['sp4', 'sp5']
        }
        
        filtered_df = pd.DataFrame(filtered_data)
        excluded_df = pd.DataFrame(excluded_data)
        
        # Generate report
        report = generate_snr_report(filtered_df, excluded_df)
        
        # Verify report structure
        assert report is not None
        assert 'total_records' in report
        assert 'filtered_count' in report
        assert 'excluded_count' in report
        assert 'mean_snr_filtered' in report
        assert 'mean_snr_excluded' in report
        
        # Verify values
        assert report['total_records'] == 5
        assert report['filtered_count'] == 3
        assert report['excluded_count'] == 2
        assert report['mean_snr_filtered'] == pytest.approx(18.33, rel=0.1)
        assert report['mean_snr_excluded'] == pytest.approx(6.5, rel=0.1)
    
    def test_generate_snr_report_empty_filtered(self):
        """Test report generation with no filtered records."""
        filtered_df = pd.DataFrame(columns=['record_id', 'snr_db', 'species_id'])
        excluded_data = {
            'record_id': [1, 2, 3],
            'snr_db': [5.0, 3.0, 8.0],
            'species_id': ['sp1', 'sp2', 'sp3']
        }
        excluded_df = pd.DataFrame(excluded_data)
        
        report = generate_snr_report(filtered_df, excluded_df)
        
        assert report['total_records'] == 3
        assert report['filtered_count'] == 0
        assert report['excluded_count'] == 3
        assert pd.isna(report['mean_snr_filtered'])
        assert report['mean_snr_excluded'] == pytest.approx(5.33, rel=0.1)
    
    def test_generate_snr_report_empty_excluded(self):
        """Test report generation with no excluded records."""
        filtered_data = {
            'record_id': [1, 2, 3],
            'snr_db': [20.0, 15.0, 12.0],
            'species_id': ['sp1', 'sp2', 'sp3']
        }
        filtered_df = pd.DataFrame(filtered_data)
        excluded_df = pd.DataFrame(columns=['record_id', 'snr_db', 'species_id'])
        
        report = generate_snr_report(filtered_df, excluded_df)
        
        assert report['total_records'] == 3
        assert report['filtered_count'] == 3
        assert report['excluded_count'] == 0
        assert report['mean_snr_filtered'] == pytest.approx(15.67, rel=0.1)
        assert pd.isna(report['mean_snr_excluded'])
    
    def test_generate_snr_report_empty_both(self):
        """Test report generation with both datasets empty."""
        filtered_df = pd.DataFrame(columns=['record_id', 'snr_db', 'species_id'])
        excluded_df = pd.DataFrame(columns=['record_id', 'snr_db', 'species_id'])
        
        report = generate_snr_report(filtered_df, excluded_df)
        
        assert report['total_records'] == 0
        assert report['filtered_count'] == 0
        assert report['excluded_count'] == 0
        assert pd.isna(report['mean_snr_filtered'])
        assert pd.isna(report['mean_snr_excluded'])

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_snr_calculation_with_extreme_values(self):
        """Test SNR calculation with extreme signal/noise ratios."""
        # Very high SNR (signal >> noise)
        signal_power = 100.0
        noise_power = 0.001
        
        with patch('src.data.preprocessing.librosa') as mock_librosa:
            mock_librosa.feature.rms.return_value = np.array([np.sqrt(signal_power)])
            mock_librosa.core.stft.return_value = np.array([[np.sqrt(noise_power)]])
            
            mock_audio_path = "/fake/path/audio.wav"
            result = calculate_snr(mock_audio_path)
            
            assert result is not None
            assert result > 40  # Should be very high SNR
    
    def test_filter_with_single_record(self):
        """Test filtering with single record dataset."""
        data = {
            'record_id': [1],
            'snr_db': [15.0],
            'species_id': ['sp1']
        }
        df = pd.DataFrame(data)
        
        # Passes threshold
        filtered_df, excluded_df = filter_by_snr(df, threshold_db=10.0)
        assert len(filtered_df) == 1
        assert len(excluded_df) == 0
        
        # Fails threshold
        filtered_df, excluded_df = filter_by_snr(df, threshold_db=20.0)
        assert len(filtered_df) == 0
        assert len(excluded_df) == 1
    
    def test_filter_preserves_original_data(self):
        """Test that filtering doesn't modify the original dataframe."""
        original_data = {
            'record_id': [1, 2, 3, 4, 5],
            'snr_db': [25.0, 15.0, 8.0, 12.0, 5.0],
            'species_id': ['sp1', 'sp2', 'sp3', 'sp4', 'sp5'],
            'extra_col': ['a', 'b', 'c', 'd', 'e']
        }
        df = pd.DataFrame(original_data)
        df_copy = df.copy()
        
        filter_by_snr(df, threshold_db=10.0)
        
        # Verify original dataframe is unchanged
        pd.testing.assert_frame_equal(df, df_copy)
    
    def test_snr_threshold_boundary(self):
        """Test filtering exactly at the threshold boundary."""
        data = {
            'record_id': [1, 2, 3],
            'snr_db': [10.0, 9.999, 10.001],
            'species_id': ['sp1', 'sp2', 'sp3']
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded_df = filter_by_snr(df, threshold_db=10.0)
        
        # Record with exactly 10.0 should be excluded (<= threshold)
        # Record with 10.001 should be included (> threshold)
        assert len(filtered_df) == 1
        assert len(excluded_df) == 2
        
        assert filtered_df['snr_db'].iloc[0] == 10.001
        assert set(excluded_df['snr_db'].tolist()) == {10.0, 9.999}

if __name__ == '__main__':
    pytest.main([__file__, '-v'])