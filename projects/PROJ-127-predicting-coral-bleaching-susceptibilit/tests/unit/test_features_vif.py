import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.features import calculate_vif, filter_high_vif, check_definitional_circularity

class TestVIF:
    def test_vif_calculation_low_correlation(self):
        """Test VIF calculation with uncorrelated features."""
        df = pd.DataFrame({
            'feature_a': np.random.normal(0, 1, 100),
            'feature_b': np.random.normal(0, 1, 100),
            'feature_c': np.random.normal(0, 1, 100),
            'target': np.random.randint(0, 2, 100)
        })
        
        vif_df = calculate_vif(df, ['feature_a', 'feature_b', 'feature_c'])
        
        # With uncorrelated features, VIF should be close to 1
        assert all(vif_df['vif'] < 2.0), "VIF should be low for uncorrelated features"
        assert len(vif_df) == 3

    def test_vif_calculation_high_correlation(self):
        """Test VIF calculation with highly correlated features."""
        base = np.random.normal(0, 1, 100)
        df = pd.DataFrame({
            'feature_a': base,
            'feature_b': base * 1.1 + np.random.normal(0, 0.1, 100), # Highly correlated
            'feature_c': np.random.normal(0, 1, 100),
            'target': np.random.randint(0, 2, 100)
        })
        
        vif_df = calculate_vif(df, ['feature_a', 'feature_b', 'feature_c'])
        
        # feature_a and feature_b should have high VIF
        high_vif_features = vif_df[vif_df['vif'] > 5.0]
        assert len(high_vif_features) >= 1, "At least one feature should have high VIF"

    def test_filter_high_vif(self):
        """Test filtering of high VIF features."""
        vif_df = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3', 'f4'],
            'vif': [1.2, 6.5, 3.0, 10.0]
        })
        
        keep = filter_high_vif(vif_df, threshold=5.0)
        
        assert 'f1' in keep
        assert 'f3' in keep
        assert 'f2' not in keep
        assert 'f4' not in keep
        assert len(keep) == 2

    def test_circularity_check_drops_dhw(self):
        """Test that DHW is dropped if SST is present (circularity)."""
        df = pd.DataFrame({
            'sst': [28.0, 29.0, 30.0],
            'dhw': [1.0, 2.0, 3.0],
            'other': [10, 20, 30],
            'target': [0, 1, 0]
        })
        
        log_path = Path("/tmp/test_circ_log.md")
        result = check_definitional_circularity(df, log_path)
        
        assert 'dhw' not in result.columns, "DHW should be dropped"
        assert 'sst' in result.columns, "SST should remain"
        assert 'circularity_check_flag' in result.columns
        assert result['circularity_check_flag'].iloc[0] == "DROP"
        
        # Cleanup
        if log_path.exists():
            log_path.unlink()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])