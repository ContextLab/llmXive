import pytest
import json
import sys
from pathlib import Path

# Add code root to path
_code_root = Path(__file__).resolve().parent.parent.parent / "code"
if str(_code_root) not in sys.path:
    sys.path.insert(0, str(_code_root))

from analysis.power_analysis import calculate_n_for_power, run_power_analysis, _calculate_n_for_lmm
from utils.logging import StatisticalAnalysisError

class TestPowerAnalysis:
    
    def test_calculate_n_basic(self):
        """Test basic N calculation with default parameters."""
        result = calculate_n_for_power(
            effect_size=0.5,
            power=0.8,
            alpha=0.05,
            intraclass_correlation=0.3,
            n_timepoints=100
        )
        
        assert "calculated_N" in result
        assert result["effect_size"] == 0.5
        assert result["power"] == 0.8
        assert result["alpha"] == 0.05
        assert result["beta"] == 0.2
        assert result["calculated_N"] > 0
        assert isinstance(result["calculated_N"], int)

    def test_effect_size_impact(self):
        """Test that smaller effect size requires larger N."""
        n_large_effect = calculate_n_for_power(effect_size=1.0, power=0.8)["calculated_N"]
        n_medium_effect = calculate_n_for_power(effect_size=0.5, power=0.8)["calculated_N"]
        n_small_effect = calculate_n_for_power(effect_size=0.2, power=0.8)["calculated_N"]
        
        assert n_small_effect > n_medium_effect
        assert n_medium_effect > n_large_effect

    def test_power_impact(self):
        """Test that higher power requires larger N."""
        n_low_power = calculate_n_for_power(effect_size=0.5, power=0.6)["calculated_N"]
        n_high_power = calculate_n_for_power(effect_size=0.5, power=0.9)["calculated_N"]
        
        assert n_high_power > n_low_power

    def test_icc_impact(self):
        """Test that higher ICC increases required N due to VIF."""
        n_low_icc = calculate_n_for_power(effect_size=0.5, power=0.8, intraclass_correlation=0.1)["calculated_N"]
        n_high_icc = calculate_n_for_power(effect_size=0.5, power=0.8, intraclass_correlation=0.5)["calculated_N"]
        
        assert n_high_icc > n_low_icc

    def test_invalid_power(self):
        """Test that invalid power values raise error."""
        with pytest.raises(StatisticalAnalysisError):
            _calculate_n_for_lmm(effect_size=0.5, power=1.5)
        
        with pytest.raises(StatisticalAnalysisError):
            _calculate_n_for_lmm(effect_size=0.5, power=0.0)

    def test_invalid_effect_size(self):
        """Test that non-positive effect size raises error."""
        with pytest.raises(StatisticalAnalysisError):
            _calculate_n_for_lmm(effect_size=0.0, power=0.8)
        
        with pytest.raises(StatisticalAnalysisError):
            _calculate_n_for_lmm(effect_size=-0.5, power=0.8)

    def test_output_json_structure(self):
        """Test that run_power_analysis produces valid JSON output."""
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_power_report.json"
            results = run_power_analysis(
                effect_size=0.5,
                power=0.8,
                output_path=str(output_path)
            )
            
            # Verify file exists
            assert output_path.exists()
            
            # Verify JSON content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "calculated_N" in data
            assert "effect_size" in data
            assert "method" in data
            assert data["method"] == "LMM_approximation_with_VIF"

    def test_vif_calculation(self):
        """Test Variance Inflation Factor logic."""
        # VIF = 1 + (k-1)*rho
        # For k=100, rho=0.3 -> VIF = 1 + 99*0.3 = 30.7
        # For k=10, rho=0.3 -> VIF = 1 + 9*0.3 = 3.7
        
        n_large_k = calculate_n_for_power(effect_size=0.5, power=0.8, n_timepoints=100)["calculated_N"]
        n_small_k = calculate_n_for_power(effect_size=0.5, power=0.8, n_timepoints=10)["calculated_N"]
        
        # Larger number of timepoints per subject increases VIF, thus increasing N
        # Note: The relationship might not be strictly linear due to the approximation
        assert n_large_k > n_small_k
