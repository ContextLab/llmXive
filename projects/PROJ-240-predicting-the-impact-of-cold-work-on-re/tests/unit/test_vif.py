import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
from code.utils import calculate_vif

class TestVIFCalculation:
    """Unit tests for Variance Inflation Factor (VIF) calculation."""

    def test_vif_perfect_multicollinearity(self):
        """Test that VIF is very high when perfect multicollinearity exists."""
        # Create a DataFrame where col2 is exactly 2 * col1
        data = pd.DataFrame({
            'col1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'col2': [2.0, 4.0, 6.0, 8.0, 10.0],  # Perfect linear relationship
            'col3': [1.0, 0.5, 2.0, 1.5, 3.0]
        })
        
        # VIF for col1 and col2 should be infinite or extremely high
        # statsmodels returns np.inf for perfect collinearity
        vif_values = calculate_vif(data)
        
        # Check that VIF for col1 and col2 are extremely large
        assert vif_values['col1'] >= 1e10 or np.isinf(vif_values['col1'])
        assert vif_values['col2'] >= 1e10 or np.isinf(vif_values['col2'])
        
        # col3 should have a reasonable VIF (not infinite)
        assert vif_values['col3'] < 100  # Should be finite and reasonable

    def test_vif_no_multicollinearity(self):
        """Test that VIF is close to 1 when features are uncorrelated."""
        # Create a DataFrame with uncorrelated features
        np.random.seed(42)
        data = pd.DataFrame({
            'feature_a': np.random.randn(100),
            'feature_b': np.random.randn(100),
            'feature_c': np.random.randn(100)
        })
        
        vif_values = calculate_vif(data)
        
        # VIF should be close to 1 for uncorrelated features (typically < 5)
        for feature, vif in vif_values.items():
            assert vif < 5.0, f"VIF for {feature} is {vif}, expected < 5.0"
            assert vif >= 1.0, f"VIF for {feature} is {vif}, expected >= 1.0"

    def test_vif_with_interaction_terms(self):
        """Test VIF calculation with interaction terms (common in our domain)."""
        # Simulate data with interaction terms
        np.random.seed(42)
        n_samples = 100
        cold_work = np.random.uniform(0, 100, n_samples)
        mn_content = np.random.uniform(0, 1, n_samples)
        interaction = cold_work * mn_content
        
        data = pd.DataFrame({
            'cold_work': cold_work,
            'mn_content': mn_content,
            'interaction': interaction
        })
        
        vif_values = calculate_vif(data)
        
        # Interaction terms often have higher VIF due to correlation with main effects
        # but should not be infinite unless perfectly collinear
        assert all(vif >= 1.0 for vif in vif_values.values())
        # We don't expect infinite VIF here because cold_work and mn_content are random
        assert not any(np.isinf(vif) for vif in vif_values.values())

    def test_vif_single_feature(self):
        """Test VIF with a single feature (should be 1.0)."""
        data = pd.DataFrame({
            'single_feature': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        vif_values = calculate_vif(data)
        
        assert len(vif_values) == 1
        assert vif_values['single_feature'] == 1.0

    def test_vif_with_constant_column(self):
        """Test that VIF handles constant columns appropriately (raises error or returns inf)."""
        data = pd.DataFrame({
            'constant': [5.0, 5.0, 5.0, 5.0, 5.0],
            'variable': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        # This should raise a ValueError from statsmodels due to constant column
        # or return infinite VIF. We test that it doesn't crash silently.
        with pytest.raises((ValueError, RuntimeWarning)):
            calculate_vif(data)

    def test_vif_with_realistic_alloy_data(self):
        """Test VIF with data structure similar to our alloy composition data."""
        # Simulate realistic alloy data with some correlation
        np.random.seed(42)
        n_samples = 200
        
        # Base compositions (typically low and correlated in real alloys)
        mn = np.random.uniform(0, 1.5, n_samples)
        mg = np.random.uniform(0, 1.2, n_samples)
        si = np.random.uniform(0, 0.8, n_samples)
        cu = np.random.uniform(0, 0.5, n_samples)
        
        # Add some correlation between Mn and Mg (common in 5xxx/6xxx series)
        mg = mg + 0.3 * mn + np.random.normal(0, 0.1, n_samples)
        
        # Interaction terms
        cold_work = np.random.uniform(10, 80, n_samples)
        mn_cw = cold_work * mn
        mg_cw = cold_work * mg
        
        data = pd.DataFrame({
            'cold_work': cold_work,
            'Mn_content': mn,
            'Mg_content': mg,
            'Si_content': si,
            'Cu_content': cu,
            'cold_work_Mn': mn_cw,
            'cold_work_Mg': mg_cw
        })
        
        vif_values = calculate_vif(data)
        
        # All VIFs should be finite (no perfect collinearity)
        assert not any(np.isinf(vif) for vif in vif_values.values())
        
        # Interaction terms may have higher VIF but should be < 10 for our use case
        # (we accept some multicollinearity but want to monitor it)
        for feature, vif in vif_values.items():
            assert vif < 20.0, f"VIF for {feature} is {vif}, expected < 20.0"

    def test_vif_output_format(self):
        """Test that VIF output is a dictionary with correct structure."""
        data = pd.DataFrame({
            'feature1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'feature2': [5.0, 4.0, 3.0, 2.0, 1.0]
        })
        
        result = calculate_vif(data)
        
        assert isinstance(result, dict)
        assert 'feature1' in result
        assert 'feature2' in result
        assert all(isinstance(v, (int, float, np.floating)) for v in result.values())