"""
Unit tests for binning utilities.
"""
import pytest
import numpy as np
from code.utils.binning_utils import define_density_bins


class TestDefineDensityBins:
    """Tests for the define_density_bins function."""

    def test_basic_quantile_split(self):
        """Test that values are split into low, med, high correctly."""
        # Create a known distribution: 0-33 low, 34-66 med, 67-100 high
        values = [i / 100.0 for i in range(100)]
        labels = define_density_bins(values)

        # Check counts are roughly equal
        assert labels.count('low') == 34  # 0-33 inclusive
        assert labels.count('med') == 33  # 34-66 inclusive
        assert labels.count('high') == 33  # 67-99 inclusive

    def test_edge_values(self):
        """Test that min and max values are assigned correctly."""
        values = [0.0, 0.5, 1.0]
        labels = define_density_bins(values)

        assert labels[0] == 'low'  # Min value
        assert labels[2] == 'high'  # Max value
        # Middle value depends on distribution, but should be valid
        assert labels[1] in ['low', 'med', 'high']

    def test_single_value(self):
        """Test behavior with a single value."""
        values = [0.5]
        labels = define_density_bins(values)
        assert labels == ['low']  # Single value falls in the first bin

    def test_duplicate_values(self):
        """Test that duplicate values get the same label."""
        values = [0.2, 0.2, 0.2, 0.8, 0.8, 0.8]
        labels = define_density_bins(values)
        assert labels[0] == labels[1] == labels[2]
        assert labels[3] == labels[4] == labels[5]
        assert labels[0] != labels[3]

    def test_numpy_array_input(self):
        """Test that numpy arrays are accepted."""
        values = np.array([0.1, 0.5, 0.9])
        labels = define_density_bins(values)
        assert len(labels) == 3
        assert all(isinstance(l, str) for l in labels)

    def test_empty_input_raises(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError):
            define_density_bins([])

    def test_invalid_type_raises(self):
        """Test that non-list/array input raises TypeError."""
        with pytest.raises(TypeError):
            define_density_bins("not a list")

    def test_negative_value_raises(self):
        """Test that negative density raises ValueError."""
        with pytest.raises(ValueError):
            define_density_bins([-0.1, 0.5, 0.9])

    def test_value_over_one_raises(self):
        """Test that density > 1 raises ValueError."""
        with pytest.raises(ValueError):
            define_density_bins([0.1, 0.5, 1.5])

    def test_nan_value_raises(self):
        """Test that NaN value raises ValueError."""
        with pytest.raises(ValueError):
            define_density_bins([0.1, np.nan, 0.9])

    def test_deterministic_output(self):
        """Test that the same input always produces the same output."""
        values = [0.1, 0.3, 0.5, 0.7, 0.9] * 10
        labels1 = define_density_bins(values)
        labels2 = define_density_bins(values)
        assert labels1 == labels2