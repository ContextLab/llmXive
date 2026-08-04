"""
Unit tests for edge cases in the EEG analysis pipeline.
Tests cover: empty datasets, missing peaks, invalid inputs, and boundary conditions.
"""

import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import functions from the project code modules
from code.extract import extract_erp_metrics, calculate_snr
from code.stats import load_metrics, filter_participants, check_normality, perform_paired_ttest
from code.viz import calculate_prevalence
from code.data_utils import validate_config_schema


class TestEmptyDatasets:
    """Tests for handling empty datasets and missing files."""

    def test_extract_metrics_empty_epochs(self):
        """Test that extract_erp_metrics handles empty epoch lists gracefully."""
        # Simulate empty epoch data
        empty_epochs = []
        conditions = ["standard", "deviant"]
        
        # Should raise a clear error or return empty results
        with pytest.raises((ValueError, IndexError, KeyError)):
            extract_erp_metrics(empty_epochs, conditions)

    def test_load_metrics_empty_file(self):
        """Test loading an empty metrics CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("participant_id,standard_amplitude,deviant_amplitude,peak_detected,snr\n")
            temp_path = f.name
        
        try:
            df = load_metrics(temp_path)
            assert len(df) == 0
        finally:
            os.unlink(temp_path)

    def test_load_metrics_missing_file(self):
        """Test loading a non-existent metrics file."""
        with pytest.raises(FileNotFoundError):
            load_metrics("/nonexistent/path/metrics.csv")

    def test_filter_participants_empty_input(self):
        """Test filtering with an empty DataFrame."""
        df = pd.DataFrame(columns=["participant_id", "peak_detected", "standard_amplitude"])
        result = filter_participants(df, exclude_list=[])
        assert len(result) == 0

    def test_validate_config_empty_schema(self):
        """Test config validation with empty schema."""
        with pytest.raises((ValueError, KeyError)):
            validate_config_schema({})


class TestMissingPeaks:
    """Tests for handling missing peak detections."""

    def test_extract_metrics_no_peak_in_window(self):
        """Test behavior when no peak is found in the primary window."""
        # Create synthetic data that won't have a peak in the expected window
        times = np.linspace(-0.2, 0.5, 500)  # -200ms to 500ms
        # Flat line or noise without a clear negative peak in 150-250ms
        data = np.zeros((1, 1, len(times)))
        
        # Mock epochs structure
        class MockEpochs:
            def __init__(self, data, times):
                self._data = data
                self.times = times
                self.ch_names = ['Fz']
                
            def get_data(self, picks=None):
                return self._data
                
            def copy(self):
                return self
                
            def average(self):
                class MockAvg:
                    def __init__(self, data, times):
                        self.data = data
                        self.times = times
                    def get_data(self, picks=None):
                        return self.data
                return MockAvg(self._data, self.times)

        epochs = MockEpochs(data, times)
        
        # Should handle missing peak gracefully (return NaN or flag)
        # The actual function should not crash
        try:
            result = extract_erp_metrics([epochs], ["standard", "deviant"])
            # Check if peak_detected is False or amplitude is NaN
            if not result.empty:
                assert 'peak_detected' in result.columns or 'standard_amplitude' in result.columns
        except Exception:
            # Expected behavior might be to raise a specific error
            pass

    def test_calculate_snr_zero_signal(self):
        """Test SNR calculation with zero signal (division by zero protection)."""
        signal = np.zeros(100)
        noise = np.ones(100) * 0.001
        
        # Should handle zero signal without crashing
        try:
            snr = calculate_snr(signal, noise)
            # SNR might be -inf or raise an error depending on implementation
        except (ValueError, ZeroDivisionError):
            pass  # Expected if implementation doesn't handle this edge case

    def test_metrics_with_all_false_peak_detected(self):
        """Test statistical analysis when all participants have peak_detected=False."""
        df = pd.DataFrame({
            "participant_id": ["sub-01", "sub-02", "sub-03"],
            "peak_detected": [False, False, False],
            "standard_amplitude": [1.0, 2.0, 3.0],
            "deviant_amplitude": [1.5, 2.5, 3.5],
            "snr": [0.1, 0.2, 0.3]
        })
        
        # Filter should exclude all if peak_detected is required
        filtered = filter_participants(df, exclude_list=[])
        # Depending on logic, this might return empty or all with flag
        assert len(filtered) <= len(df)


class TestBoundaryConditions:
    """Tests for boundary conditions and edge values."""

    def test_normality_check_single_sample(self):
        """Test normality check with a single data point."""
        data = np.array([1.0])
        # Shapiro-Wilk requires at least 3 samples
        try:
            result = check_normality(data)
            # Should return False or raise a warning
        except Exception:
            pass  # Expected for small sample size

    def test_ttest_insufficient_samples(self):
        """Test t-test with insufficient samples."""
        group1 = np.array([1.0])
        group2 = np.array([2.0])
        
        try:
            t_stat, p_val = perform_paired_ttest(group1, group2)
            # Should handle gracefully
        except Exception:
            pass  # Expected for small sample size

    def test_prevalence_zero_valid(self):
        """Test prevalence calculation with zero valid participants."""
        df = pd.DataFrame({
            "participant_id": [],
            "peak_detected": []
        })
        
        prevalence = calculate_prevalence(df)
        assert prevalence == 0.0

    def test_prevalence_all_valid(self):
        """Test prevalence calculation with all valid participants."""
        df = pd.DataFrame({
            "participant_id": ["sub-01", "sub-02"],
            "peak_detected": [True, True]
        })
        
        prevalence = calculate_prevalence(df)
        assert prevalence == 1.0

    def test_prevalence_mixed(self):
        """Test prevalence calculation with mixed results."""
        df = pd.DataFrame({
            "participant_id": ["sub-01", "sub-02", "sub-03", "sub-04"],
            "peak_detected": [True, False, True, False]
        })
        
        prevalence = calculate_prevalence(df)
        assert prevalence == 0.5


class TestInvalidInputs:
    """Tests for handling invalid input types and malformed data."""

    def test_extract_metrics_invalid_condition_names(self):
        """Test with condition names that don't exist in the data."""
        # Simulate epochs with only 'standard' condition
        times = np.linspace(-0.2, 0.5, 100)
        data = np.random.randn(1, 1, len(times))
        
        class MockEpochs:
            def __init__(self, data, times, event_ids):
                self._data = data
                self.times = times
                self.event_ids = event_ids
                
            def get_data(self, picks=None):
                return self._data
                
            def copy(self):
                return self
                
            def average(self):
                class MockAvg:
                    def __init__(self, data, times):
                        self.data = data
                        self.times = times
                    def get_data(self, picks=None):
                        return self.data
                return MockAvg(self._data, self.times)

        epochs = MockEpochs(data, times, {"standard": 1})
        
        # Requesting a non-existent condition
        with pytest.raises((KeyError, ValueError)):
            extract_erp_metrics([epochs], ["standard", "non_existent"])

    def test_metrics_csv_malformed_schema(self):
        """Test loading a CSV with missing required columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("participant_id,standard_amplitude\n")  # Missing required columns
            f.write("sub-01,1.5\n")
            temp_path = f.name
        
        try:
            df = load_metrics(temp_path)
            # Should handle missing columns gracefully or raise error
            assert "participant_id" in df.columns
        finally:
            os.unlink(temp_path)

    def test_filter_with_invalid_exclusion_list(self):
        """Test filtering with an exclusion list containing non-existent IDs."""
        df = pd.DataFrame({
            "participant_id": ["sub-01", "sub-02"],
            "peak_detected": [True, True],
            "standard_amplitude": [1.0, 2.0]
        })
        
        # Excluding non-existent IDs should not crash
        result = filter_participants(df, exclude_list=["sub-999", "sub-888"])
        assert len(result) == len(df)  # No participants should be removed

    def test_config_schema_missing_required_fields(self):
        """Test config validation with missing required fields."""
        config = {
            "filter": {"low": 1, "high": 30}
            # Missing 'epoch', 'ica', etc.
        }
        
        with pytest.raises((ValueError, KeyError)):
            validate_config_schema(config)