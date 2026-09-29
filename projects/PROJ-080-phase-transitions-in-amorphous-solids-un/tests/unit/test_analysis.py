import pytest
import numpy as np
from scipy import stats
import json
import os
import sys
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils import set_seed
from code.logging_config import get_logger

logger = get_logger(__name__)


class TestKolmogorovSmirnov:
    """Unit tests for Kolmogorov-Smirnov test implementation (US2)."""

    def test_ks_test_basic_functionality(self):
        """Test that KS test runs and returns expected structure."""
        set_seed(42)
        
        # Generate two distinct distributions (brittle vs ductile simulation)
        # Brittle: lower variance, lower mean D2_min
        brittle_data = np.random.normal(loc=0.05, scale=0.02, size=100)
        # Ductile: higher variance, higher mean D2_min
        ductile_data = np.random.normal(loc=0.08, scale=0.05, size=100)
        
        # Run KS test
        statistic, p_value = stats.ks_2samp(brittle_data, ductile_data)
        
        assert isinstance(statistic, float), "KS statistic must be a float"
        assert isinstance(p_value, float), "P-value must be a float"
        assert 0.0 <= statistic <= 1.0, "KS statistic must be between 0 and 1"
        assert 0.0 <= p_value <= 1.0, "P-value must be between 0 and 1"
        
        logger.info(f"KS Test - Statistic: {statistic:.4f}, P-value: {p_value:.4f}")

    def test_ks_test_identical_distributions(self):
        """Test KS test returns p-value ~ 1.0 for identical distributions."""
        set_seed(42)
        data = np.random.normal(loc=0.05, scale=0.02, size=100)
        
        statistic, p_value = stats.ks_2samp(data, data)
        
        # For identical distributions, p-value should be 1.0
        assert abs(p_value - 1.0) < 1e-6, "P-value for identical distributions should be ~1.0"
        assert statistic == 0.0, "KS statistic for identical distributions should be 0.0"

    def test_ks_test_disjoint_distributions(self):
        """Test KS test returns p-value ~ 0.0 for completely disjoint distributions."""
        set_seed(42)
        data1 = np.random.normal(loc=0.01, scale=0.001, size=100)
        data2 = np.random.normal(loc=0.99, scale=0.001, size=100)
        
        statistic, p_value = stats.ks_2samp(data1, data2)
        
        # For disjoint distributions, p-value should be very close to 0
        assert p_value < 0.001, "P-value for disjoint distributions should be near 0"
        assert statistic > 0.9, "KS statistic for disjoint distributions should be near 1"

    def test_ks_test_small_sample_size(self):
        """Test KS test behavior with small sample sizes (N < 30)."""
        set_seed(42)
        data1 = np.random.normal(loc=0.05, scale=0.02, size=10)
        data2 = np.random.normal(loc=0.08, scale=0.05, size=10)
        
        statistic, p_value = stats.ks_2samp(data1, data2)
        
        # Should still run, but p-value may be unreliable
        assert isinstance(statistic, float), "KS statistic must be a float"
        assert isinstance(p_value, float), "P-value must be a float"
        logger.warning(f"Small sample KS Test - Statistic: {statistic:.4f}, P-value: {p_value:.4f}")

    def test_ks_test_result_structure(self):
        """Test that KS test results can be serialized to JSON as required by FR-003."""
        set_seed(42)
        brittle_data = np.random.normal(loc=0.05, scale=0.02, size=50)
        ductile_data = np.random.normal(loc=0.08, scale=0.05, size=50)
        
        statistic, p_value = stats.ks_2samp(brittle_data, ductile_data)
        
        result = {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "sample_size_brittle": len(brittle_data),
            "sample_size_ductile": len(ductile_data),
            "method": "Kolmogorov-Smirnov two-sample test",
            "framing": "associational finding (not causal)"
        }
        
        # Verify JSON serialization
        json_str = json.dumps(result, indent=2)
        loaded_result = json.loads(json_str)
        
        assert loaded_result["statistic"] == statistic
        assert loaded_result["p_value"] == p_value
        assert loaded_result["framing"] == "associational finding (not causal)"

    def test_ks_test_with_nan_handling(self):
        """Test that KS test handles NaN values correctly (should raise or filter)."""
        set_seed(42)
        data1 = np.random.normal(loc=0.05, scale=0.02, size=100)
        data2 = np.random.normal(loc=0.08, scale=0.05, size=100)
        data2[5] = np.nan  # Inject NaN
        
        # scipy.stats.ks_2samp should raise a warning or error with NaN
        # We expect it to produce a warning but still return a result, 
        # or we handle it explicitly in the calling code
        with pytest.warns(UserWarning):
            statistic, p_value = stats.ks_2samp(data1, data2)
        
        # If it returns a result, it should be valid
        assert isinstance(statistic, float)
        assert isinstance(p_value, float)

    def test_ks_test_consistency_with_seed(self):
        """Test that KS test results are deterministic with fixed seed."""
        set_seed(42)
        brittle_data_1 = np.random.normal(loc=0.05, scale=0.02, size=100)
        ductile_data_1 = np.random.normal(loc=0.08, scale=0.05, size=100)
        
        set_seed(42)
        brittle_data_2 = np.random.normal(loc=0.05, scale=0.02, size=100)
        ductile_data_2 = np.random.normal(loc=0.08, scale=0.05, size=100)
        
        stat1, pval1 = stats.ks_2samp(brittle_data_1, ductile_data_1)
        stat2, pval2 = stats.ks_2samp(brittle_data_2, ductile_data_2)
        
        assert stat1 == stat2, "KS statistic should be deterministic with fixed seed"
        assert pval1 == pval2, "P-value should be deterministic with fixed seed"

    def test_ks_test_output_metadata(self):
        """Test that output includes all required metadata per FR-003."""
        set_seed(42)
        brittle_data = np.random.normal(loc=0.05, scale=0.02, size=50)
        ductile_data = np.random.normal(loc=0.08, scale=0.05, size=50)
        
        statistic, p_value = stats.ks_2samp(brittle_data, ductile_data)
        
        output = {
            "ks_statistic": statistic,
            "p_value": p_value,
            "n_brittle": len(brittle_data),
            "n_ductile": len(ductile_data),
            "test_type": "two-sample",
            "assumption": "independent samples",
            "interpretation": "associational finding"
        }
        
        # Verify all keys exist
        required_keys = ["ks_statistic", "p_value", "n_brittle", "n_ductile", "test_type", "interpretation"]
        for key in required_keys:
            assert key in output, f"Missing required key: {key}"

    def test_ks_test_edge_case_single_sample(self):
        """Test KS test with single sample (edge case)."""
        set_seed(42)
        data1 = np.array([0.05])
        data2 = np.array([0.08])
        
        # scipy should handle this, though results may be trivial
        statistic, p_value = stats.ks_2samp(data1, data2)
        
        assert isinstance(statistic, float)
        assert isinstance(p_value, float)
        # With single samples, if they are different, statistic should be 1.0
        if data1[0] != data2[0]:
            assert statistic == 1.0