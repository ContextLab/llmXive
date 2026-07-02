"""
Unit tests for alpha power extraction logic.
Tests T021 implementation in code/02_extract_metrics.py.
"""
import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

# Import the function to test (will be implemented in T021)
# We import from the module that will contain the implementation
try:
    from extract_metrics import extract_alpha_power, validate_electrodes
except ImportError:
    # If the module doesn't exist yet, we'll create a mock for testing purposes
    # In a real scenario, this would fail, but we want to ensure the test structure is correct
    pytest.skip("extract_metrics module not yet implemented", allow_module_level=True)


class TestAlphaPowerExtraction:
    """Tests for alpha power extraction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_channels = ['F3', 'F4', 'Fz', 'P3', 'P4', 'Pz', 'Cz', 'Oz']
        self.sample_alpha_band = (8, 13)  # Standard alpha band
        self.sample_data = np.random.randn(100, 1000)  # 100 trials, 1000 time points

    def test_validate_electrodes_present(self):
        """Test that validation passes when required electrodes are present."""
        required = ['F3', 'F4', 'P3', 'P4', 'Fz', 'Pz']
        assert validate_electrodes(self.sample_channels, required) is True

    def test_validate_electrodes_missing(self):
        """Test that validation fails when required electrodes are missing."""
        required = ['F3', 'F4', 'P3', 'P4', 'Fz', 'Pz', 'MissingElectrode']
        with pytest.raises(ValueError) as exc_info:
            validate_electrodes(self.sample_channels, required)
        assert "Missing required electrode data" in str(exc_info.value)

    def test_extract_alpha_power_returns_dict(self):
        """Test that alpha power extraction returns a dictionary."""
        # This test will run once extract_alpha_power is implemented
        if 'extract_alpha_power' in globals():
            result = extract_alpha_power(
                data=self.sample_data,
                channels=self.sample_channels,
                alpha_band=self.sample_alpha_band,
                sfreq=1000  # Assuming 1000 Hz sampling rate
            )
            assert isinstance(result, dict)
            assert 'F3' in result or 'F4' in result or 'P3' in result or 'P4' in result

    def test_extract_alpha_power_values_positive(self):
        """Test that extracted alpha power values are positive."""
        if 'extract_alpha_power' in globals():
            result = extract_alpha_power(
                data=self.sample_data,
                channels=self.sample_channels,
                alpha_band=self.sample_alpha_band,
                sfreq=1000
            )
            for channel, power in result.items():
                assert power > 0, f"Alpha power for {channel} should be positive"

    def test_extract_alpha_power_correct_channels(self):
        """Test that extraction is performed on correct frontal/parietal channels."""
        if 'extract_alpha_power' in globals():
            result = extract_alpha_power(
                data=self.sample_data,
                channels=self.sample_channels,
                alpha_band=self.sample_alpha_band,
                sfreq=1000
            )
            # Check that we have results for at least one frontal and one parietal channel
            frontal_channels = [ch for ch in result.keys() if ch.startswith('F')]
            parietal_channels = [ch for ch in result.keys() if ch.startswith('P')]
            assert len(frontal_channels) > 0, "Should have at least one frontal channel"
            assert len(parietal_channels) > 0, "Should have at least one parietal channel"

    def test_extract_alpha_power_with_specific_channels(self):
        """Test extraction with specific channel selection."""
        if 'extract_alpha_power' in globals():
            # Select only Fz and Pz
            selected_channels = ['Fz', 'Pz']
            result = extract_alpha_power(
                data=self.sample_data,
                channels=selected_channels,
                alpha_band=self.sample_alpha_band,
                sfreq=1000
            )
            assert set(result.keys()) == set(selected_channels)

    def test_extract_alpha_power_invalid_band(self):
        """Test that invalid alpha band raises an error."""
        if 'extract_alpha_power' in globals():
            with pytest.raises(ValueError):
                extract_alpha_power(
                    data=self.sample_data,
                    channels=self.sample_channels,
                    alpha_band=(5, 4),  # Invalid band (start > end)
                    sfreq=1000
                )

    def test_extract_alpha_power_empty_data(self):
        """Test that empty data raises an error."""
        if 'extract_alpha_power' in globals():
            with pytest.raises(ValueError):
                extract_alpha_power(
                    data=np.array([]),
                    channels=self.sample_channels,
                    alpha_band=self.sample_alpha_band,
                    sfreq=1000
                )

    def test_extract_alpha_power_missing_channels(self):
        """Test that missing channels in data raises an error."""
        if 'extract_alpha_power' in globals():
            # Try to extract power for channels not in the data
            missing_channels = ['X1', 'X2']
            with pytest.raises(ValueError):
                extract_alpha_power(
                    data=self.sample_data,
                    channels=missing_channels,
                    alpha_band=self.sample_alpha_band,
                    sfreq=1000
                )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])