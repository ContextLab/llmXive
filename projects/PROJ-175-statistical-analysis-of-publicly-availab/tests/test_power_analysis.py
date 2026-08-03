"""
Tests for T013b: Power Analysis.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Import the module under test
# Adjust import path based on project structure
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.power_analysis import calculate_sample_size, calculate_variance_estimate

class TestPowerAnalysis:
    
    def test_calculate_sample_size_basic(self):
        """Test basic sample size calculation."""
        variance = 1.0
        effect_size = 0.5 # Large effect
        n = calculate_sample_size(variance, effect_size=effect_size)
        
        # With large effect size, n should be relatively small
        assert n > 0
        assert isinstance(n, int)
    
    def test_calculate_sample_size_small_effect(self):
        """Test that small effect size requires larger sample."""
        variance = 1.0
        n_large = calculate_sample_size(variance, effect_size=0.5)
        n_small = calculate_sample_size(variance, effect_size=0.1)
        
        assert n_small > n_large
    
    def test_calculate_variance_estimate_with_ratings(self):
        """Test variance estimation when 'rating' column exists."""
        data = {"rating": [1.0, 2.0, 3.0, 4.0, 5.0]}
        df = pd.DataFrame(data)
        var = calculate_variance_estimate(df)
        # Variance of [1,2,3,4,5] is 2.5
        assert abs(var - 2.5) < 0.01
    
    def test_calculate_variance_estimate_with_ingredients(self):
        """Test variance estimation when 'ingredients' list column exists."""
        data = {"ingredients": [[1], [1, 2], [1, 2, 3], [1], [1, 2]]}
        df = pd.DataFrame(data)
        var = calculate_variance_estimate(df)
        # Counts: [1, 2, 3, 1, 2] -> mean=1.8, var=0.7
        assert var > 0
    
    def test_calculate_variance_estimate_fallback(self):
        """Test variance estimation fallback when no numeric columns."""
        data = {"name": ["A", "B", "C"]}
        df = pd.DataFrame(data)
        var = calculate_variance_estimate(df)
        # Should fallback to 0.25
        assert abs(var - 0.25) < 0.01

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
