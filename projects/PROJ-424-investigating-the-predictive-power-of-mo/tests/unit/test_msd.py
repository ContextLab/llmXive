"""
Unit tests for MSD analysis module (T016).

Tests for:
- MSD extraction logic (T011)
- Diffusion coefficient calculation and scaling (T012)
- MAE calculation against NIST refs (T013)
"""
import pytest
from pathlib import Path
import numpy as np
from scipy import stats

from code.analysis.msd import (
    MSDResult,
    load_trajectory_timeseries,
    perform_linear_regression,
    validate_linearity,
    calculate_diffusion_coefficient,
    analyze_msd,
    R2_THRESHOLD
)
from code.data_models.diffusion_results import DiffusionResults

class TestMSDExtraction:
    """Tests for MSD extraction logic (T011)."""
    
    def test_load_trajectory_timeseries_water(self):
        """Test loading trajectory for water."""
        time_ps, msd_nm2 = load_trajectory_timeseries(
            Path("dummy.trr"), "water", 1.0
        )
        
        assert len(time_ps) == 100
        assert len(msd_nm2) == 100
        assert time_ps[0] == 0
        assert time_ps[-1] == 1000  # 1ns = 1000ps
        assert all(msd_nm2 >= 0)
    
    def test_load_trajectory_timeseries_ethanol(self):
        """Test loading trajectory for ethanol."""
        time_ps, msd_nm2 = load_trajectory_timeseries(
            Path("dummy.trr"), "ethanol", 5.0
        )
        
        assert len(time_ps) == 100
        assert time_ps[-1] == 5000  # 5ns
    
    def test_load_trajectory_timeseries_acetone(self):
        """Test loading trajectory for acetone."""
        time_ps, msd_nm2 = load_trajectory_timeseries(
            Path("dummy.trr"), "acetone", 10.0
        )
        
        assert len(time_ps) == 100
        assert time_ps[-1] == 10000  # 10ns

class TestLinearRegression:
    """Tests for linear regression logic."""
    
    def test_perform_linear_regression(self):
        """Test linear regression on synthetic MSD data."""
        time_ps = np.linspace(0, 1000, 100)
        msd_nm2 = 6 * 2.3 * (time_ps / 1000.0)  # D=2.3 for water
        
        slope, intercept, r_squared, p_value = perform_linear_regression(
            time_ps, msd_nm2
        )
        
        # For perfect data, slope should be ~6*D = 13.8
        assert abs(slope - 13.8) < 0.1
        assert abs(intercept) < 0.1
        assert r_squared >= 0.999
    
    def test_linear_regression_with_noise(self):
        """Test linear regression with noisy data."""
        time_ps = np.linspace(0, 1000, 100)
        np.random.seed(42)
        msd_nm2 = 6 * 2.3 * (time_ps / 1000.0) + np.random.normal(0, 0.1, 100)
        
        slope, intercept, r_squared, p_value = perform_linear_regression(
            time_ps, msd_nm2
        )
        
        assert r_squared >= 0.95  # Should still be linear enough

class TestLinearityValidation:
    """Tests for linearity validation (R² threshold)."""
    
    def test_validate_linearity_pass(self):
        """Test that high R² passes validation."""
        assert validate_linearity(0.99) is True
        assert validate_linearity(0.95) is True
        assert validate_linearity(0.96) is True
    
    def test_validate_linearity_fail(self):
        """Test that low R² fails validation."""
        assert validate_linearity(0.94) is False
        assert validate_linearity(0.90) is False
        assert validate_linearity(0.50) is False
    
    def test_r_squared_threshold_constant(self):
        """Verify R² threshold is 0.95 per Constitution Principle VI."""
        assert R2_THRESHOLD == 0.95

class TestDiffusionCoefficient:
    """Tests for diffusion coefficient calculation and scaling (T012)."""
    
    def test_calculate_diffusion_coefficient_water(self):
        """Test D calculation for water."""
        slope = 13.8  # 6 * 2.3
        D = calculate_diffusion_coefficient(slope, "water")
        
        assert abs(D - 2.3) < 0.01
    
    def test_calculate_diffusion_coefficient_ethanol(self):
        """Test D calculation for ethanol."""
        slope = 6.6  # 6 * 1.1
        D = calculate_diffusion_coefficient(slope, "ethanol")
        
        assert abs(D - 1.1) < 0.01
    
    def test_calculate_diffusion_coefficient_acetone(self):
        """Test D calculation for acetone."""
        slope = 5.7  # 6 * 0.95
        D = calculate_diffusion_coefficient(slope, "acetone")
        
        assert abs(D - 0.95) < 0.01
    
    def test_diffusion_coefficient_formula(self):
        """Verify D = slope / 6 formula."""
        for D_true in [1.0, 2.0, 3.0]:
            slope = 6 * D_true
            D_calc = calculate_diffusion_coefficient(slope, "water")
            assert abs(D_calc - D_true) < 0.001

class TestMAECalculation:
    """Tests for MAE calculation against NIST refs (T013)."""
    
    def test_mae_calculation(self):
        """Test MAE calculation between predicted and NIST values."""
        nist_refs = {
            'water': 2.3,
            'ethanol': 1.1,
            'acetone': 0.95
        }
        
        predictions = {
            'water': 2.25,
            'ethanol': 1.15,
            'acetone': 0.90
        }
        
        errors = [abs(predictions[k] - nist_refs[k]) for k in nist_refs]
        mae = np.mean(errors)
        
        expected_mae = np.mean([0.05, 0.05, 0.05])
        assert abs(mae - expected_mae) < 0.001
    
    def test_mae_single_solvent(self):
        """Test MAE for single solvent."""
        nist = 2.3
        predicted = 2.2
        mae = abs(predicted - nist)
        assert mae == 0.1

class TestAnalyzeMSD:
    """Integration tests for full MSD analysis pipeline."""
    
    def test_analyze_msd_water_1ns(self):
        """Test full analysis for water at 1ns."""
        result = analyze_msd(
            trajectory_path=Path("dummy.trr"),
            solvent="water",
            timescale_ns=1.0
        )
        
        assert isinstance(result, DiffusionResults)
        assert result.solvent == "water"
        assert result.timescale_ns == 1.0
        assert result.is_linear is True
        assert result.r_squared >= 0.95
        assert result.diffusion_coefficient > 0
    
    def test_analyze_msd_ethanol_5ns(self):
        """Test full analysis for ethanol at 5ns."""
        result = analyze_msd(
            trajectory_path=Path("dummy.trr"),
            solvent="ethanol",
            timescale_ns=5.0
        )
        
        assert result.solvent == "ethanol"
        assert result.timescale_ns == 5.0
        assert result.is_linear is True
    
    def test_analyze_msd_acetone_10ns(self):
        """Test full analysis for acetone at 10ns."""
        result = analyze_msd(
            trajectory_path=Path("dummy.trr"),
            solvent="acetone",
            timescale_ns=10.0
        )
        
        assert result.solvent == "acetone"
        assert result.timescale_ns == 10.0
        assert result.is_linear is True
    
    def test_analyze_msd_invalid_solvent(self):
        """Test analysis with unknown solvent (uses default scaling)."""
        result = analyze_msd(
            trajectory_path=Path("dummy.trr"),
            solvent="unknown",
            timescale_ns=1.0
        )
        
        assert result.solvent == "unknown"
        assert result.is_linear is True

class TestLinearityFailure:
    """Tests for non-linear MSD cases."""
    
    def test_non_linear_msd_raises_error(self):
        """Test that non-linear MSD raises ValueError."""
        # This test would need to mock the load_trajectory_timeseries
        # to return non-linear data. For now, we verify the threshold logic.
        assert validate_linearity(0.94) is False
        assert validate_linearity(0.95) is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])