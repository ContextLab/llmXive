import json
import numpy as np
import pytest
from pathlib import Path
import tempfile
import os

# Import the functions to test
from statistical_analyzer import (
    calculate_anisotropy_deviation,
    bootstrap_confidence_interval,
    generate_null_bootstrap_distribution
)

class TestCalculateAnisotropyDeviation:
    def test_deviation_positive(self):
        """Test deviation calculation when observed > null."""
        observed = 0.8
        null = 0.5
        expected = abs(0.8 - 0.5)
        assert calculate_anisotropy_deviation(observed, null) == expected

    def test_deviation_negative(self):
        """Test deviation calculation when observed < null."""
        observed = 0.3
        null = 0.5
        expected = abs(0.3 - 0.5)
        assert calculate_anisotropy_deviation(observed, null) == expected

    def test_deviation_zero(self):
        """Test deviation calculation when observed == null."""
        observed = 0.5
        null = 0.5
        assert calculate_anisotropy_deviation(observed, null) == 0.0

class TestBootstrapConfidenceInterval:
    def test_ci_calculation(self):
        """Test CI calculation on a known distribution."""
        # Create a deterministic distribution
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        ci = bootstrap_confidence_interval(data, confidence_level=1.0) # Full range
        
        assert ci["lower"] == 1.0
        assert ci["upper"] == 5.0
        assert ci["mean"] == 3.0

    def test_ci_empty_data(self):
        """Test that empty data raises an error."""
        with pytest.raises(ValueError):
            bootstrap_confidence_interval([])

class TestGenerateNullBootstrapDistribution:
    def test_bootstrap_length(self):
        """Test that the output length matches n_bootstrap."""
        similarities = {"pair1": 0.5, "pair2": 0.6}
        n_bootstrap = 100
        seed = 42
        
        dist = generate_null_bootstrap_distribution(similarities, n_bootstrap, seed)
        
        assert len(dist) == n_bootstrap

    def test_bootstrap_values_range(self):
        """Test that bootstrap values are within the range of input values."""
        similarities = {"pair1": 0.5, "pair2": 0.6}
        n_bootstrap = 100
        seed = 42
        
        dist = generate_null_bootstrap_distribution(similarities, n_bootstrap, seed)
        
        min_val = min(similarities.values())
        max_val = max(similarities.values())
        
        for val in dist:
            assert min_val <= val <= max_val
