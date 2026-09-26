"""
Unit tests for the power analysis module (T059).
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.power import (
    estimate_mdes_kinetic,
    estimate_mdes_correlation,
    calculate_effect_size,
    PowerAnalysisError
)

class TestKineticPowerAnalysis:
    def test_mdes_kinetic_n3(self):
        """Test MDES calculation for n=3 replicates."""
        result = estimate_mdes_kinetic(n_replicates=3)
        
        assert "mdes_ns" in result
        assert result["n_replicates"] == 3
        assert result["assumed_sigma_ns"] == 0.05
        assert result["alpha"] == 0.05
        assert result["power"] == 0.80
        assert result["mdes_ns"] > 0
        assert "interpretation" in result
        assert "limitation" in result

    def test_mdes_kinetic_n5(self):
        """Test MDES calculation for n=5 replicates (should be lower than n=3)."""
        result_n3 = estimate_mdes_kinetic(n_replicates=3)
        result_n5 = estimate_mdes_kinetic(n_replicates=5)
        
        assert result_n5["mdes_ns"] < result_n3["mdes_ns"], "MDES should decrease with more replicates"

    def test_mdes_kinetic_invalid_n(self):
        """Test that n < 2 raises an error."""
        with pytest.raises(PowerAnalysisError):
            estimate_mdes_kinetic(n_replicates=1)

class TestCorrelationPowerAnalysis:
    def test_mdes_correlation_n5(self):
        """Test MDES calculation for n=5 solvents."""
        result = estimate_mdes_correlation(n_solvents=5)
        
        assert "mdes_slope" in result
        assert result["n_solvents"] == 5
        assert result["assumed_sigma_y_ns"] == 0.5
        assert result["assumed_sigma_x_index"] == 0.3
        assert result["alpha"] == 0.05
        assert result["power"] == 0.80
        assert result["mdes_slope"] > 0
        assert "interpretation" in result
        assert "limitation" in result

    def test_mdes_correlation_n8(self):
        """Test MDES calculation for n=8 solvents (should be lower than n=5)."""
        result_n5 = estimate_mdes_correlation(n_solvents=5)
        result_n8 = estimate_mdes_correlation(n_solvents=8)
        
        assert result_n8["mdes_slope"] < result_n5["mdes_slope"], "MDES should decrease with more solvents"

    def test_mdes_correlation_invalid_n(self):
        """Test that n < 3 raises an error."""
        with pytest.raises(PowerAnalysisError):
            estimate_mdes_correlation(n_solvents=2)

class TestEffectSizeCalculation:
    def test_calculate_effect_size(self):
        """Test the combined effect size calculation."""
        result = calculate_effect_size(n_replicates=3, n_solvents=5)
        
        assert "kinetic_analysis" in result
        assert "correlation_analysis" in result
        assert "study_design" in result
        assert result["study_design"]["n_replicates_per_solvent"] == 3
        assert result["study_design"]["n_solvent_conditions"] == 5
        assert result["study_design"]["total_measurements"] == 15

if __name__ == "__main__":
    pytest.main([__file__, "-v"])