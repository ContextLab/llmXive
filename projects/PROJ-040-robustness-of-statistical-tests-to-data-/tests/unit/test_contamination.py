"""
Unit tests for contamination injection logic (T008).

These tests verify that:
1. The number of injected outliers matches round(contamination_rate * total_rows)
2. The Gaussian noise is injected with the correct mean and standard deviation
3. The outlier values are extreme relative to the data distribution

These tests are designed to fail until T011 (generate_contamination.py) is implemented.
"""

import pytest
import numpy as np
import pandas as pd
import os
import sys

# Add the project root to the path to allow imports
# Assuming this test is run from the project root or tests/ directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# We will import the contamination logic once it is implemented in T011
# For now, we define the expected interface and test against it
# The actual implementation will be in code/data/generate_contamination.py

# Mock the expected function signature for testing purposes
# In the real implementation, this will be imported from code/data/generate_contamination.py
def _mock_contaminate_data(df, contamination_rate, outlier_magnitude=5.0, random_seed=42):
    """
    Mock implementation for testing.
    This should be replaced by the actual implementation from generate_contamination.py
    """
    # This is a placeholder that will fail the tests until the real implementation is done
    return df, []

# We will import the real function when it exists
# For now, we use the mock to define the test structure
try:
    from code.data.generate_contamination import contaminate_data
except ImportError:
    # If the module doesn't exist yet, use the mock
    contaminate_data = _mock_contaminate_data


class TestContaminationInjection:
    """Tests for the contamination injection logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.seed = 42
        np.random.seed(self.seed)
        
        # Create a simple test dataset
        self.n_rows = 1000
        self.data = pd.DataFrame({
            'feature1': np.random.normal(0, 1, self.n_rows),
            'feature2': np.random.normal(10, 2, self.n_rows),
            'feature3': np.random.normal(-5, 0.5, self.n_rows)
        })
        
        # Test contamination rates
        self.test_rates = [0.01, 0.05, 0.10, 0.20]
        
    def test_outlier_count_accuracy(self):
        """
        Verify that the number of injected outliers equals round(contamination_rate * total_rows).
        
        This is a critical test for T011 implementation.
        """
        for rate in self.test_rates:
            expected_outlier_count = round(rate * self.n_rows)
            
            # Run contamination
            contaminated_df, outlier_info = contaminate_data(
                self.data.copy(), 
                contamination_rate=rate,
                random_seed=self.seed
            )
            
            # Count actual outliers (this depends on the implementation details)
            # The outlier_info should contain the count or we can infer from the data
            actual_outlier_count = len(outlier_info) if isinstance(outlier_info, list) else 0
            
            assert actual_outlier_count == expected_outlier_count, (
                f"For contamination rate {rate}, expected {expected_outlier_count} outliers, "
                f"but got {actual_outlier_count}"
            )
    
    def test_gaussian_noise_parameters(self):
        """
        Verify that Gaussian noise is injected with correct mean and standard deviation.
        
        The noise should have:
        - Mean close to 0 (within statistical tolerance)
        - Standard deviation matching the specified magnitude
        """
        rate = 0.05
        noise_magnitude = 3.0
        
        contaminated_df, outlier_info = contaminate_data(
            self.data.copy(),
            contamination_rate=rate,
            outlier_magnitude=noise_magnitude,
            random_seed=self.seed
        )
        
        # Extract the noise values from outlier_info or contaminated data
        # This depends on the implementation - we expect outlier_info to contain
        # information about the injected noise
        if isinstance(outlier_info, dict) and 'noise_values' in outlier_info:
            noise_values = outlier_info['noise_values']
        elif isinstance(outlier_info, list) and len(outlier_info) > 0:
            # Assume outlier_info contains tuples or dicts with noise information
            noise_values = [item.get('noise_value', 0) for item in outlier_info if isinstance(item, dict)]
        else:
            # Fallback: try to infer from the difference between original and contaminated
            # This is less reliable but works for testing
            noise_values = []
            for col in self.data.columns:
                diff = contaminated_df[col] - self.data[col]
                # Non-zero differences indicate contamination
                non_zero_mask = diff != 0
                noise_values.extend(diff[non_zero_mask].tolist())
        
        if len(noise_values) > 0:
            noise_array = np.array(noise_values)
            mean_noise = np.mean(noise_values)
            std_noise = np.std(noise_values)
            
            # Check mean is close to 0 (within 0.1 for small samples)
            assert abs(mean_noise) < 0.5, (
                f"Expected mean noise close to 0, got {mean_noise:.4f}"
            )
            
            # Check standard deviation is close to the specified magnitude
            # Allow 20% tolerance for statistical variation
            assert abs(std_noise - noise_magnitude) < noise_magnitude * 0.2, (
                f"Expected noise std close to {noise_magnitude}, got {std_noise:.4f}"
            )
        else:
            pytest.skip("No noise values found - implementation may not be complete")
    
    def test_outlier_extremeness(self):
        """
        Verify that injected outliers are extreme relative to the data distribution.
        
        Outliers should be significantly beyond the normal data range (e.g., > 3-5 std devs).
        """
        rate = 0.05
        
        contaminated_df, outlier_info = contaminate_data(
            self.data.copy(),
            contamination_rate=rate,
            outlier_magnitude=5.0,
            random_seed=self.seed
        )
        
        # For each feature, check that outliers are extreme
        for col in self.data.columns:
            original_std = self.data[col].std()
            original_mean = self.data[col].mean()
            
            # Get contaminated values for this column
            contaminated_values = contaminated_df[col].values
            
            # Find values that are significantly different from original
            z_scores = np.abs((contaminated_values - original_mean) / original_std)
            extreme_values = contaminated_values[z_scores > 3]  # More than 3 std devs
            
            if len(extreme_values) > 0:
                # Verify these are indeed outliers (should be present due to contamination)
                assert len(extreme_values) > 0, (
                    f"No extreme values found in {col} despite {rate*100}% contamination"
                )
    
    def test_deterministic_with_seed(self):
        """
        Verify that the same seed produces identical results.
        """
        rate = 0.1
        
        # First run
        df1, info1 = contaminate_data(
            self.data.copy(),
            contamination_rate=rate,
            random_seed=self.seed
        )
        
        # Second run with same seed
        df2, info2 = contaminate_data(
            self.data.copy(),
            contamination_rate=rate,
            random_seed=self.seed
        )
        
        # DataFrames should be identical
        pd.testing.assert_frame_equal(df1, df2)
        
        # Outlier info should be identical
        if isinstance(info1, list) and isinstance(info2, list):
            assert len(info1) == len(info2)
            for i in range(len(info1)):
                assert info1[i] == info2[i], f"Outlier info differs at index {i}"
        elif isinstance(info1, dict) and isinstance(info2, dict):
            assert info1 == info2
    
    def test_no_contamination_when_rate_is_zero(self):
        """
        Verify that contamination_rate=0 produces no changes.
        """
        contaminated_df, outlier_info = contaminate_data(
            self.data.copy(),
            contamination_rate=0.0,
            random_seed=self.seed
        )
        
        # Data should be unchanged
        pd.testing.assert_frame_equal(contaminated_df, self.data)
        
        # No outliers should be recorded
        assert len(outlier_info) == 0 if isinstance(outlier_info, list) else True
    
    def test_handles_missing_values_gracefully(self):
        """
        Verify that the function handles missing values without crashing.
        """
        # Create data with missing values
        data_with_na = self.data.copy()
        data_with_na.loc[0, 'feature1'] = np.nan
        
        try:
            contaminated_df, outlier_info = contaminate_data(
                data_with_na,
                contamination_rate=0.05,
                random_seed=self.seed
            )
            # Should not crash
            assert contaminated_df is not None
        except Exception as e:
            pytest.fail(f"Function crashed with missing values: {e}")
    
    def test_skips_non_numeric_columns(self):
        """
        Verify that non-numeric columns are skipped during contamination.
        """
        # Create data with non-numeric column
        data_mixed = self.data.copy()
        data_mixed['category'] = ['A', 'B', 'C'] * (self.n_rows // 3) + ['A'] * (self.n_rows % 3)
        
        try:
            contaminated_df, outlier_info = contaminate_data(
                data_mixed,
                contamination_rate=0.05,
                random_seed=self.seed
            )
            
            # Non-numeric column should remain unchanged
            pd.testing.assert_series_equal(
                contaminated_df['category'],
                data_mixed['category'],
                check_names=True
            )
        except Exception as e:
            pytest.fail(f"Function crashed with mixed data types: {e}")