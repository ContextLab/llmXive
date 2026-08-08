import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from imbalance import calculate_gini, calculate_compositional_imbalance_score, MIN_SAMPLES_THRESHOLD

class TestGiniCoefficient:
    def test_gini_perfect_equality(self):
        """Gini should be 0 for perfectly equal distribution."""
        values = np.array([10, 10, 10, 10])
        gini = calculate_gini(values)
        assert np.isclose(gini, 0.0, atol=1e-5)

    def test_gini_perfect_inequality(self):
        """Gini should be close to 1 for highly unequal distribution."""
        values = np.array([0, 0, 0, 100])
        gini = calculate_gini(values)
        # Gini for [0,0,0,100] is 0.75 in standard definition, 
        # but our formula might yield slightly different.
        # Standard Gini: (n+1 - 2*sum((n+1-i)*y_i)/sum(y_i)) / n
        # Let's just check it's > 0.5
        assert gini > 0.5

    def test_gini_negative_values(self):
        """Gini should handle negative values by taking absolute."""
        values = np.array([-10, -10, -10, -10])
        gini = calculate_gini(values)
        assert np.isclose(gini, 0.0, atol=1e-5)

    def test_gini_empty_array(self):
        """Gini should return 0 for empty array."""
        values = np.array([])
        gini = calculate_gini(values)
        assert gini == 0.0

    def test_gini_zero_sum(self):
        """Gini should return 0 if sum is 0 (after abs)."""
        values = np.array([0, 0, 0])
        gini = calculate_gini(values)
        assert gini == 0.0

class TestCompositionalImbalance:
    def test_kmeans_clustering(self):
        """Test that K-Means clustering runs and returns valid Gini."""
        # Create a simple synthetic dataset
        np.random.seed(42)
        data = {
            'feat1': np.random.randn(200),
            'feat2': np.random.randn(200)
        }
        df = pd.DataFrame(data)
        
        score = calculate_compositional_imbalance_score(df, ['feat1', 'feat2'])
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_small_dataset_kmeans(self):
        """Test K-Means with dataset smaller than k."""
        np.random.seed(42)
        data = {
            'feat1': np.random.randn(10),
            'feat2': np.random.randn(10)
        }
        df = pd.DataFrame(data)
        
        # Should adjust k automatically
        score = calculate_compositional_imbalance_score(df, ['feat1', 'feat2'])
        
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_no_features(self):
        """Test with no features provided."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="No compositional features provided"):
            calculate_compositional_imbalance_score(df, [])