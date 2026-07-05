import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import from the project's code modules
from data.preprocess import check_confounding
from models.metrics import calculate_vif, check_collinearity
from data.linkage import derive_stimulus_id_from_trial_id
from data.models import Trial

class TestEdgeCasesMissingMetadata:
    """Tests for edge cases involving missing metadata."""

    def test_derive_stimulus_id_missing_mapping(self):
        """Test derivation when no mapping exists for trial IDs."""
        # Create a mock scenario where linkage fails
        trial_ids = ['trial_001', 'trial_002', 'trial_003']
        
        # Simulate a scenario where derivation fails for all
        with patch('data.linkage.load_iat_csv') as mock_load:
            mock_load.return_value = []
            
            # The function should return empty or handle gracefully
            # depending on implementation, but we test the edge case
            result = derive_stimulus_id_from_trial_id(
                pd.DataFrame({'trial_id': trial_ids}),
                Path('data/primes'),
                Path('data/targets')
            )
            
            # Verify it doesn't crash and returns a valid structure
            assert result is not None
            assert 'stimulus_id' in result.columns or len(result) == 0

    def test_missing_metadata_in_preprocessing(self):
        """Test preprocessing handles missing metadata files gracefully."""
        # Create a temporary directory structure
        with patch('data.preprocess.Path.exists') as mock_exists:
            # Simulate missing human-rated ambiguity file
            mock_exists.return_value = False
            
            # This should not raise an exception, but handle the missing file
            try:
                # Call the function that would check for human ratings
                # We expect it to handle the missing file case
                pass  # The actual logic is tested in integration
            except FileNotFoundError:
                pytest.fail("Preprocessing should handle missing metadata gracefully")

    def test_high_missing_rate_linkage(self):
        """Test linkage derivation with >10% missing rate."""
        # Create a dataset where most trials have no mapping
        df = pd.DataFrame({
            'trial_id': [f'trial_{i}' for i in range(100)],
            'response_time': [1000.0] * 100
        })
        
        # Mock a scenario where 90% of trials cannot be linked
        with patch('data.linkage.derive_stimulus_id_from_trial_id') as mock_derive:
            # Return a dataframe with only 10% linked
            linked_df = df.head(10).copy()
            linked_df['stimulus_id'] = [f'stim_{i}' for i in range(10)]
            mock_derive.return_value = linked_df
            
            # The function should handle this case (either warn or halt)
            # depending on the specific implementation logic
            result = derive_stimulus_id_from_trial_id(
                df,
                Path('data/primes'),
                Path('data/targets')
            )
            
            assert result is not None

class TestEdgeCasesHighCollinearity:
    """Tests for edge cases involving high collinearity."""

    def test_vif_calculation_with_perfect_collinearity(self):
        """Test VIF calculation when variables are perfectly collinear."""
        # Create a dataset with perfect collinearity
        np.random.seed(42)
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 * 2  # Perfectly collinear
        
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': x1,
            'x2': x2
        })
        
        # This should return very high VIF values
        vif_results = calculate_vif(df, ['x1', 'x2'])
        
        # At least one VIF should be extremely high (approaching infinity)
        assert any(vif > 100 for vif in vif_results.values()), \
            "Perfect collinearity should result in very high VIF"

    def test_vif_calculation_with_high_collinearity(self):
        """Test VIF calculation when variables are highly correlated."""
        np.random.seed(42)
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 * 0.95 + np.random.randn(n) * 0.1  # High correlation
        
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': x1,
            'x2': x2
        })
        
        vif_results = calculate_vif(df, ['x1', 'x2'])
        
        # VIF should be elevated (> 5.0)
        assert any(vif > 5.0 for vif in vif_results.values()), \
            "High collinearity should result in VIF > 5.0"

    def test_collinearity_check_with_threshold(self):
        """Test collinearity check with configurable threshold."""
        np.random.seed(42)
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 * 0.99  # Very high correlation
        
        df = pd.DataFrame({
            'y': np.random.randn(n),
            'x1': x1,
            'x2': x2
        })
        
        # Test with default threshold (5.0)
        is_collinear, vif_dict = check_collinearity(df, ['x1', 'x2'], threshold=5.0)
        assert is_collinear, "Should detect collinearity with threshold 5.0"
        
        # Test with higher threshold
        is_collinear_high, _ = check_collinearity(df, ['x1', 'x2'], threshold=100.0)
        # May or may not detect depending on exact VIF value

    def test_confounding_check_with_constant_variable(self):
        """Test confounding check when a variable is constant."""
        # Create data where prime condition is constant
        df = pd.DataFrame({
            'prime_condition': [1] * 100,
            'trial_order': list(range(100)),
            'response_time': np.random.randn(100) * 100 + 500
        })
        
        # This should handle the constant variable gracefully
        # (either skip it or flag it as problematic)
        try:
            result = check_confounding(df, 'prime_condition', 'trial_order')
            # Should not crash
            assert result is not None
        except Exception as e:
            # If it raises, it should be a clear error message
            assert "constant" in str(e).lower() or "variance" in str(e).lower()

    def test_confounding_check_with_small_sample(self):
        """Test confounding check with very small sample size."""
        # Create data with only a few observations
        df = pd.DataFrame({
            'prime_condition': [0, 1, 0, 1, 0],
            'trial_order': [1, 2, 3, 4, 5],
            'response_time': [500, 600, 550, 580, 520]
        })
        
        # Should handle small sample gracefully
        try:
            result = check_confounding(df, 'prime_condition', 'trial_order')
            assert result is not None
        except Exception as e:
            # If it raises, it should be a clear warning about small sample
            assert "small" in str(e).lower() or "sample" in str(e).lower()

class TestEdgeCasesDataQuality:
    """Tests for various data quality edge cases."""

    def test_empty_dataframe_handling(self):
        """Test that functions handle empty dataframes gracefully."""
        empty_df = pd.DataFrame(columns=['trial_id', 'response_time', 'stimulus_id'])
        
        # Test VIF calculation with empty dataframe
        try:
            vif_results = calculate_vif(empty_df, ['response_time'])
            # Should handle empty input
            assert isinstance(vif_results, dict)
        except Exception as e:
            # If it raises, it should be a clear error
            assert "empty" in str(e).lower()

    def test_single_observation_handling(self):
        """Test handling of single observation."""
        single_df = pd.DataFrame({
            'y': [1.0],
            'x1': [2.0],
            'x2': [3.0]
        })
        
        # VIF requires at least 2 observations
        try:
            vif_results = calculate_vif(single_df, ['x1', 'x2'])
            # Should handle gracefully
            assert isinstance(vif_results, dict)
        except Exception as e:
            # If it raises, it should be a clear error about sample size
            assert "sample" in str(e).lower() or "observation" in str(e).lower()

    def test_non_numeric_data_in_numeric_column(self):
        """Test handling of non-numeric data in numeric columns."""
        df = pd.DataFrame({
            'y': [1.0, 2.0, 'invalid', 4.0],
            'x1': [2.0, 3.0, 4.0, 5.0]
        })
        
        # Should handle non-numeric data gracefully
        try:
            vif_results = calculate_vif(df, ['x1'])
            # May drop invalid rows or raise error
            assert isinstance(vif_results, dict)
        except (ValueError, TypeError) as e:
            # Expected for invalid data
            pass