import os
import sys
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.kinetic_fit import (
    exponential_decay,
    fit_single_decay,
    calculate_confidence_interval,
    process_trace_file,
    run_global_kinetic_analysis,
    perform_threshold_sensitivity_analysis
)

class TestExponentialDecay:
    """Test the exponential decay model function."""
    
    def test_exponential_decay_basic(self):
        """Test basic exponential decay calculation."""
        t = np.array([0, 1, 2, 3, 4, 5])
        A, tau, offset = 10.0, 2.0, 1.0
        
        expected = A * np.exp(-t / tau) + offset
        actual = exponential_decay(t, A, tau, offset)
        
        np.testing.assert_array_almost_equal(actual, expected)
    
    def test_exponential_decay_limits(self):
        """Test decay approaches offset at large t."""
        t = np.array([0, 10, 100])
        A, tau, offset = 10.0, 2.0, 1.0
        
        result = exponential_decay(t, A, tau, offset)
        
        # At t=0, should be A + offset = 11
        assert result[0] == pytest.approx(11.0, rel=1e-5)
        # At large t, should approach offset = 1
        assert result[2] == pytest.approx(1.0, rel=1e-2)

class TestFitSingleDecay:
    """Test single exponential decay fitting."""
    
    def test_fit_perfect_data(self):
        """Test fitting on perfect synthetic data."""
        t = np.linspace(0, 10, 100)
        A_true, tau_true, offset_true = 5.0, 1.5, 0.5
        y_true = exponential_decay(t, A_true, tau_true, offset_true)
        
        # Add small noise
        np.random.seed(42)
        y_noisy = y_true + np.random.normal(0, 0.01, size=y_true.shape)
        
        tau_fit, tau_std, fit_info = fit_single_decay(t, y_noisy)
        
        # Should recover tau within 10%
        assert abs(tau_fit - tau_true) / tau_true < 0.1
        assert fit_info['r_squared'] > 0.99
    
    def test_fit_with_initial_guess(self):
        """Test fitting with custom initial guess."""
        t = np.linspace(0, 10, 100)
        A_true, tau_true, offset_true = 8.0, 2.5, 0.2
        y_true = exponential_decay(t, A_true, tau_true, offset_true)
        
        np.random.seed(42)
        y_noisy = y_true + np.random.normal(0, 0.02, size=y_true.shape)
        
        initial_guess = {'A': 10.0, 'tau': 2.0, 'offset': 0.5}
        tau_fit, tau_std, fit_info = fit_single_decay(t, y_noisy, initial_guess)
        
        assert abs(tau_fit - tau_true) / tau_true < 0.15
        assert fit_info['r_squared'] > 0.95
    
    def test_fit_convergence_error(self):
        """Test that fitting fails appropriately on bad data."""
        t = np.array([0, 1, 2])
        y = np.array([1, 1, 1])  # Flat line, cannot fit decay
        
        with pytest.raises(ValueError):
            fit_single_decay(t, y)
    
    def test_fit_nan_handling(self):
        """Test fitting with NaN values."""
        t = np.array([0, 1, 2, 3, 4])
        y = np.array([5.0, np.nan, 3.0, 2.0, 1.0])
        
        # Should handle NaN gracefully (filter them out)
        tau_fit, tau_std, fit_info = fit_single_decay(t, y)
        
        assert tau_fit > 0
        assert tau_std > 0

class TestCalculateConfidenceInterval:
    """Test confidence interval calculation."""
    
    def test_ci_calculation(self):
        """Test basic CI calculation."""
        tau = 2.0
        tau_std = 0.1
        n_replicates = 3
        
        ci_lower, ci_upper = calculate_confidence_interval(tau, tau_std, n_replicates)
        
        # Should be symmetric around tau
        assert ci_lower < tau < ci_upper
        assert abs((ci_lower + ci_upper) / 2 - tau) < 1e-10
    
    def test_ci_with_single_replicate(self):
        """Test CI with n=1 (should still work with dof=1)."""
        tau = 2.0
        tau_std = 0.1
        
        ci_lower, ci_upper = calculate_confidence_interval(tau, tau_std, n_replicates=1)
        
        assert ci_lower < tau < ci_upper
    
    def test_ci_confidence_level(self):
        """Test that higher confidence gives wider intervals."""
        tau = 2.0
        tau_std = 0.1
        
        ci_95_lower, ci_95_upper = calculate_confidence_interval(tau, tau_std, confidence_level=0.95)
        ci_99_lower, ci_99_upper = calculate_confidence_interval(tau, tau_std, confidence_level=0.99)
        
        # 99% CI should be wider than 95% CI
        assert (ci_99_upper - ci_99_lower) > (ci_95_upper - ci_95_lower)

class TestProcessTraceFile:
    """Test trace file processing."""
    
    def test_process_valid_file(self):
        """Test processing a valid trace file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("time_us,absorbance\n")
            for t in np.linspace(0, 10, 50):
                y = 5.0 * np.exp(-t / 2.0) + 0.5 + np.random.normal(0, 0.01)
                f.write(f"{t:.4f},{y:.4f}\n")
            temp_path = Path(f.name)
        
        try:
            result = process_trace_file(temp_path)
            
            assert 'tau' in result
            assert 'tau_std' in result
            assert 'r_squared' in result
            assert result['tau'] > 0
            assert result['r_squared'] > 0.9
        finally:
            temp_path.unlink()
    
    def test_process_missing_columns(self):
        """Test processing file with missing required columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("time,signal\n")
            f.write("0,1\n")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError):
                process_trace_file(temp_path)
        finally:
            temp_path.unlink()
    
    def test_process_insufficient_points(self):
        """Test processing file with too few points."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("time_us,absorbance\n")
            f.write("0,1\n")
            f.write("1,0.8\n")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError):
                process_trace_file(temp_path)
        finally:
            temp_path.unlink()

class TestRunGlobalKineticAnalysis:
    """Test global kinetic analysis."""
    
    def test_global_analysis_basic(self):
        """Test basic global kinetic analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "calibrated_traces.csv"
            output_path = Path(tmpdir) / "kinetic_results.csv"
            
            # Create synthetic data for 2 solvents with 3 replicates each
            np.random.seed(42)
            data = []
            
            solvents = ['hexane', 'acetonitrile']
            for solvent in solvents:
                for replicate in range(3):
                    t = np.linspace(0, 10, 50)
                    tau_true = 1.5 if solvent == 'hexane' else 2.5
                    y = 5.0 * np.exp(-t / tau_true) + 0.5 + np.random.normal(0, 0.02, size=t.shape)
                    
                    for ti, yi in zip(t, y):
                        data.append({
                            'solvent': solvent,
                            'replicate': replicate,
                            'time_us': ti,
                            'absorbance': yi
                        })
            
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            summary = run_global_kinetic_analysis(input_path, output_path)
            
            assert summary['status'] == 'success'
            assert summary['n_solvents'] == 2
            assert summary['n_total_fits'] == 6
            
            # Verify output file exists and has content
            assert output_path.exists()
            result_df = pd.read_csv(output_path)
            assert len(result_df) == 6
            assert 'tau' in result_df.columns
            assert 'r_squared' in result_df.columns
    
    def test_global_analysis_missing_input(self):
        """Test analysis with missing input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.csv"
            output_path = Path(tmpdir) / "kinetic_results.csv"
            
            with pytest.raises(FileNotFoundError):
                run_global_kinetic_analysis(input_path, output_path)
    
    def test_global_analysis_invalid_columns(self):
        """Test analysis with invalid column names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "calibrated_traces.csv"
            output_path = Path(tmpdir) / "kinetic_results.csv"
            
            df = pd.DataFrame({'wrong_col': [1, 2, 3]})
            df.to_csv(input_path, index=False)
            
            with pytest.raises(ValueError):
                run_global_kinetic_analysis(input_path, output_path)

class TestPerformThresholdSensitivityAnalysis:
    """Test threshold sensitivity analysis."""
    
    def test_sensitivity_analysis_basic(self):
        """Test basic sensitivity analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "calibrated_traces.csv"
            output_path = Path(tmpdir) / "sensitivity_results.csv"
            
            # Create synthetic data for 3 solvents with distinct lifetimes
            np.random.seed(42)
            data = []
            
            solvents = ['hexane', 'toluene', 'acetonitrile']
            taus = [1.0, 1.5, 2.5]  # Distinct lifetimes
            
            for solvent, tau_true in zip(solvents, taus):
                for replicate in range(3):
                    t = np.linspace(0, 10, 50)
                    y = 5.0 * np.exp(-t / tau_true) + 0.5 + np.random.normal(0, 0.02, size=t.shape)
                    
                    for ti, yi in zip(t, y):
                        data.append({
                            'solvent': solvent,
                            'replicate': replicate,
                            'time_us': ti,
                            'absorbance': yi
                        })
            
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            result = perform_threshold_sensitivity_analysis(
                input_path, 
                output_path,
                threshold_range=[0.1, 0.5, 1.0]
            )
            
            assert result['status'] == 'success'
            assert result['n_thresholds'] == 3
            
            # Verify output file
            assert output_path.exists()
            result_df = pd.read_csv(output_path)
            assert 'threshold' in result_df.columns
            assert 'false_positive_rate' in result_df.columns

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
