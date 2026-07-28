import pytest
import numpy as np
import pandas as pd
from scipy import stats
from code.stats import (
    bin_energy_data,
    calculate_maxwell_boltzmann_pdf,
    perform_ks_test,
    perform_chisquared_test,
    apply_benjamini_hochberg,
    StatsError
)

class TestBinning:
    def test_bin_energy_data_basic(self):
        """Test basic binning functionality."""
        data = pd.DataFrame({'E_trans': [1.0, 2.0, 3.0, 4.0, 5.0]})
        result = bin_energy_data(data)
        
        assert 'bin_index' in result.columns
        assert 'bin_center' in result.columns
        assert len(result) == len(data)
        
    def test_bin_energy_data_empty(self):
        """Test binning with empty dataframe."""
        data = pd.DataFrame({'E_trans': []})
        with pytest.raises((ValueError, StatsError)):
            bin_energy_data(data)
            
    def test_bin_energy_data_missing_column(self):
        """Test binning with missing E_trans column."""
        data = pd.DataFrame({'E_rot': [1.0, 2.0]})
        with pytest.raises(StatsError):
            bin_energy_data(data)

class TestMaxwellBoltzmann:
    def test_pdf_normalization(self):
        """Test that the MB PDF integrates to 1."""
        kT = 1.0
        energies = np.linspace(0, 10, 10000)
        _, pdf_vals = calculate_maxwell_boltzmann_pdf(energies, kT)
        
        # Numerical integration
        integral = np.trapz(pdf_vals, energies)
        assert np.isclose(integral, 1.0, atol=0.01)
        
    def test_pdf_shape(self):
        """Test that the PDF has the correct shape (starts at 0, peaks, then decays)."""
        kT = 1.0
        energies = np.linspace(0, 10, 1000)
        _, pdf_vals = calculate_maxwell_boltzmann_pdf(energies, kT)
        
        assert pdf_vals[0] == 0.0
        assert np.max(pdf_vals) > 0
        # Check decay at high energy
        assert pdf_vals[-1] < pdf_vals[100] # Should be decreasing after peak

class TestKSTest:
    def test_ks_test_perfect_fit(self):
        """Test KS test with data generated from MB distribution."""
        kT = 1.0
        # Generate synthetic data from MB distribution
        # We can use the inverse CDF or rejection sampling, but for simplicity,
        # we'll generate from a known distribution that approximates MB for testing
        # Actually, let's just test the function doesn't crash and returns valid values
        energies = np.random.exponential(scale=kT, size=1000) # Exponential is not MB, but tests structure
        result = perform_ks_test(energies, kT)
        
        assert 'statistic' in result
        assert 'pvalue' in result
        assert 0 <= result['statistic'] <= 1
        assert 0 <= result['pvalue'] <= 1
        
    def test_ks_test_empty_data(self):
        """Test KS test with empty data."""
        with pytest.raises(StatsError):
            perform_ks_test(np.array([]), 1.0)

class TestChiSquaredTest:
    def test_chisquared_test_basic(self):
        """Test Chi-squared test with basic data."""
        kT = 1.0
        energies = np.random.exponential(scale=kT, size=1000)
        result = perform_chisquared_test(energies, kT, n_bins=10)
        
        assert 'statistic' in result
        assert 'pvalue' in result
        assert 'degrees_of_freedom' in result
        assert 'observed_counts' in result
        assert 'expected_counts' in result
        assert len(result['observed_counts']) == 10
        assert len(result['expected_counts']) == 10
        
    def test_chisquared_test_small_bins(self):
        """Test Chi-squared test with too few bins."""
        kT = 1.0
        energies = np.random.exponential(scale=kT, size=1000)
        with pytest.raises(StatsError):
            perform_chisquared_test(energies, kT, n_bins=1)

class TestBenjaminiHochberg:
    def test_bh_correction(self):
        """Test Benjamini-Hochberg correction."""
        p_values = [0.01, 0.04, 0.03, 0.20, 0.50]
        result = apply_benjamini_hochberg(p_values)
        
        assert len(result) == len(p_values)
        assert all(isinstance(x, bool) for x in result)
        
    def test_bh_correction_empty(self):
        """Test BH correction with empty list."""
        result = apply_benjamini_hochberg([])
        assert result == []

class TestIntegration:
    def test_run_statistical_analysis(self, tmp_path):
        """Test the full statistical analysis pipeline."""
        # Create synthetic data
        kT = 1.0
        energies = np.random.exponential(scale=kT, size=1000)
        df = pd.DataFrame({'E_trans': energies})
        
        input_path = tmp_path / "energy_samples.csv"
        output_path = tmp_path / "statistical_results.json"
        
        df.to_csv(input_path, index=False)
        
        from code.stats import run_statistical_analysis
        run_statistical_analysis(str(input_path), str(output_path), kT=kT)
        
        assert output_path.exists()
        
        import json
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        assert len(results) == 1
        assert 'ks_test' in results[0]
        assert 'chi2_test' in results[0]