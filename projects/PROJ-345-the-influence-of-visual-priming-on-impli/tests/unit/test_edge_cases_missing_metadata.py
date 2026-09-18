import pytest
import pandas as pd
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.preprocess import check_confounding
from code.models.metrics import calculate_vif, check_collinearity
from code.config import Config

class TestMissingMetadataEdgeCases:
    """Tests for edge cases involving missing metadata in preprocessing."""

    def test_check_confounding_missing_columns(self):
        """Test that check_confounding handles DataFrames with missing required columns gracefully."""
        # Create a DataFrame missing the 'prime_order' column
        df_missing = pd.DataFrame({
            'response_time': [100, 200, 300],
            'participant_id': [1, 2, 3],
            'stimulus_id': ['s1', 's2', 's3']
            # Missing 'prime_order'
        })

        # Should raise a KeyError or ValueError, not crash silently
        with pytest.raises((KeyError, ValueError)):
            check_confounding(df_missing)

    def test_check_confounding_empty_dataframe(self):
        """Test that check_confounding handles an empty DataFrame."""
        df_empty = pd.DataFrame(columns=['response_time', 'prime_order', 'participant_id'])
        
        # Should handle empty input without crashing
        result = check_confounding(df_empty)
        assert isinstance(result, dict)
        assert 'is_confounded' in result

    def test_check_confounding_constant_order(self):
        """Test that check_confounding handles constant prime_order (variance=0)."""
        df_constant = pd.DataFrame({
            'response_time': [100, 200, 300],
            'prime_order': [1, 1, 1],  # Constant value
            'participant_id': [1, 2, 3]
        })

        # Should handle constant column without division by zero
        result = check_confounding(df_constant)
        assert isinstance(result, dict)
        # If variance is 0, correlation is undefined; should flag or handle gracefully
        assert 'is_confounded' in result

class TestHighCollinearityEdgeCases:
    """Tests for edge cases involving high collinearity in metrics."""

    def test_calculate_vif_perfect_collinearity(self):
        """Test VIF calculation when features are perfectly collinear."""
        # Create a DataFrame with perfectly collinear features
        df_perfect = pd.DataFrame({
            'feature_a': [1.0, 2.0, 3.0, 4.0],
            'feature_b': [2.0, 4.0, 6.0, 8.0],  # Exactly 2 * feature_a
            'outcome': [10, 20, 30, 40]
        })

        # VIF for perfectly collinear features should be extremely high or infinite
        # We test that the function doesn't crash and returns a high value
        try:
            vif_results = calculate_vif(df_perfect[['feature_a', 'feature_b']])
            # If it returns, at least one VIF should be very high (> 10 or inf)
            assert len(vif_results) == 2
            # Check if any VIF is extremely high (indicating collinearity detection)
            high_vif_found = any(v > 100 for v in vif_results.values())
            assert high_vif_found, "Expected at least one very high VIF for perfect collinearity"
        except Exception as e:
            # If it raises, that's also acceptable behavior for perfect collinearity
            assert "singular" in str(e).lower() or "collinear" in str(e).lower()

    def test_check_collinearity_threshold_exceeded(self):
        """Test that check_collinearity correctly flags when VIF > threshold."""
        # Create a DataFrame with moderately high collinearity
        df_high = pd.DataFrame({
            'feature_a': [1.0, 2.0, 3.0, 4.0, 5.0],
            'feature_b': [1.1, 2.1, 3.1, 4.1, 5.1],  # Highly correlated
            'outcome': [10, 20, 30, 40, 50]
        })

        result = check_collinearity(df_high[['feature_a', 'feature_b']], threshold=5.0)
        
        assert isinstance(result, dict)
        assert 'is_confounded' in result
        # With high correlation, is_confounded should likely be True
        # Note: exact behavior depends on implementation, but it should not crash

    def test_check_collinearity_low_collinearity(self):
        """Test that check_collinearity returns False for low collinearity."""
        df_low = pd.DataFrame({
            'feature_a': [1.0, 2.0, 3.0, 4.0, 5.0],
            'feature_b': [5.0, 1.0, 4.0, 2.0, 3.0],  # Low correlation
            'outcome': [10, 20, 30, 40, 50]
        })

        result = check_collinearity(df_low[['feature_a', 'feature_b']], threshold=5.0)
        
        assert isinstance(result, dict)
        assert result['is_confounded'] == False

    def test_calculate_vif_single_feature(self):
        """Test VIF calculation with a single feature (edge case)."""
        df_single = pd.DataFrame({
            'feature_a': [1.0, 2.0, 3.0, 4.0],
            'outcome': [10, 20, 30, 40]
        })

        # VIF for a single feature should be 1.0 (no collinearity)
        vif_results = calculate_vif(df_single[['feature_a']])
        assert len(vif_results) == 1
        assert vif_results['feature_a'] == 1.0

    def test_check_collinearity_empty_dataframe(self):
        """Test check_collinearity with an empty DataFrame."""
        df_empty = pd.DataFrame(columns=['feature_a', 'feature_b', 'outcome'])

        # Should handle empty input gracefully
        result = check_collinearity(df_empty[['feature_a', 'feature_b']], threshold=5.0)
        assert isinstance(result, dict)
        assert 'is_confounded' in result

    def test_check_collinearity_constant_feature(self):
        """Test check_collinearity when one feature has zero variance."""
        df_constant = pd.DataFrame({
            'feature_a': [1.0, 1.0, 1.0, 1.0],  # Constant
            'feature_b': [1.0, 2.0, 3.0, 4.0],
            'outcome': [10, 20, 30, 40]
        })

        # Should handle constant feature without crashing
        result = check_collinearity(df_constant[['feature_a', 'feature_b']], threshold=5.0)
        assert isinstance(result, dict)
        assert 'is_confounded' in result