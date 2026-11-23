"""
Unit tests for T017: Topographic correlation calculation and reporting.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the functions to test
from src.data.preprocess import (
    calculate_topographic_correlation,
    calculate_epoch_correlation,
    generate_preprocessing_report
)

# Mock MNE objects for testing
class MockEpochs:
    def __init__(self, data, ch_names, n_epochs=10):
        self.data = data  # (n_epochs, n_channels, n_times)
        self.ch_names = ch_names
        self._n_epochs = n_epochs
        
    def __len__(self):
        return self._n_epochs
        
    def __getitem__(self, idx):
        # Return a mock epoch object with get_data method
        epoch_data = self.data[idx]
        class MockEpoch:
            def get_data(self):
                return epoch_data
        return MockEpoch()


class TestT017TopographicCorrelation:
    """Test suite for topographic correlation functions."""

    def test_calculate_topographic_correlation_basic(self):
        """Test basic correlation calculation."""
        # Create identical data -> correlation should be 1.0
        n_channels = 32
        n_times = 100
        data = np.random.randn(n_channels, n_times)
        
        corr = calculate_topographic_correlation(data, data, [f'CH{i}' for i in range(n_channels)])
        assert abs(corr - 1.0) < 1e-5, f"Expected correlation ~1.0, got {corr}"

    def test_calculate_topographic_correlation_different(self):
        """Test correlation with different data."""
        n_channels = 32
        n_times = 100
        data1 = np.random.randn(n_channels, n_times)
        data2 = np.random.randn(n_channels, n_times)
        
        corr = calculate_topographic_correlation(data1, data2, [f'CH{i}' for i in range(n_channels)])
        # Just check it returns a valid number between -1 and 1
        assert -1.0 <= corr <= 1.0, f"Correlation {corr} out of bounds"

    def test_calculate_topographic_correlation_mismatched_shapes(self):
        """Test that mismatched shapes raise an error."""
        n_channels = 32
        n_times = 100
        data1 = np.random.randn(n_channels, n_times)
        data2 = np.random.randn(n_channels, n_times + 10)
        
        with pytest.raises(ValueError, match="Data shapes must match"):
            calculate_topographic_correlation(data1, data2, [f'CH{i}' for i in range(n_channels)])

    def test_calculate_epoch_correlation_basic(self):
        """Test epoch correlation calculation."""
        n_epochs = 10
        n_channels = 32
        n_times = 100
        
        # Create identical data
        data = np.random.randn(n_epochs, n_channels, n_times)
        epochs = MockEpochs(data, [f'CH{i}' for i in range(n_channels)])
        
        corr = calculate_epoch_correlation(epochs, epochs)
        assert abs(corr - 1.0) < 1e-5, f"Expected correlation ~1.0, got {corr}"

    def test_calculate_epoch_correlation_with_subset(self):
        """Test epoch correlation with channel subset."""
        n_epochs = 10
        n_channels = 32
        n_times = 100
        
        data = np.random.randn(n_epochs, n_channels, n_times)
        ch_names = [f'CH{i}' for i in range(n_channels)]
        epochs = MockEpochs(data, ch_names)
        
        # Use subset
        subset = ch_names[:16]
        corr = calculate_epoch_correlation(epochs, epochs, channel_subset=subset)
        assert abs(corr - 1.0) < 1e-5, f"Expected correlation ~1.0, got {corr}"

    def test_generate_preprocessing_report(self):
        """Test report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            
            # Create mock epochs
            n_epochs = 10
            n_channels = 32
            n_times = 100
            data = np.random.randn(n_epochs, n_channels, n_times)
            epochs = MockEpochs(data, [f'CH{i}' for i in range(n_channels)])
            
            report = generate_preprocessing_report(
                raw_epochs=epochs,
                clean_epochs=epochs,
                excluded_subjects=[],
                output_path=output_path,
                subject_id="SUBJ001"
            )
            
            # Check report structure
            assert "subject_id" in report
            assert "metrics" in report
            assert "topographic_correlation" in report["metrics"]
            assert report["subject_id"] == "SUBJ001"
            
            # Check file was created
            assert output_path.exists()
            
            # Check file content
            with open(output_path, 'r') as f:
                loaded_report = json.load(f)
            assert loaded_report["subject_id"] == "SUBJ001"
            assert "topographic_correlation" in loaded_report["metrics"]

    def test_generate_preprocessing_report_with_excluded_subjects(self):
        """Test report generation with excluded subjects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.json"
            
            # Create mock epochs
            n_epochs = 10
            n_channels = 32
            n_times = 100
            data = np.random.randn(n_epochs, n_channels, n_times)
            epochs = MockEpochs(data, [f'CH{i}' for i in range(n_channels)])
            
            excluded = ["SUBJ002", "SUBJ003"]
            report = generate_preprocessing_report(
                raw_epochs=epochs,
                clean_epochs=epochs,
                excluded_subjects=excluded,
                output_path=output_path,
                subject_id="SUBJ001"
            )
            
            assert report["excluded_subjects"] == excluded

    def test_generate_preprocessing_report_creates_file(self):
        """Test that the report file is actually created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "preprocessing_report.json"
            
            # Create mock epochs
            n_epochs = 10
            n_channels = 32
            n_times = 100
            data = np.random.randn(n_epochs, n_channels, n_times)
            epochs = MockEpochs(data, [f'CH{i}' for i in range(n_channels)])
            
            generate_preprocessing_report(
                raw_epochs=epochs,
                clean_epochs=epochs,
                excluded_subjects=[],
                output_path=output_path
            )
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0  # File is not empty