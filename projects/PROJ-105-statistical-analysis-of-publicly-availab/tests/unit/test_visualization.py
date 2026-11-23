"""
Unit tests for visualization module.
"""
import numpy as np
import pytest
from pathlib import Path
import json
import tempfile
import shutil

# Import functions to test
from visualization import (
    calculate_r2,
    empirical_survival_function,
    plot_loglog_survival,
    plot_qq_plot,
    save_r2_results
)
from models import ConvergenceError

class TestCalculateR2:
    """Tests for R² calculation."""
    
    def test_perfect_fit(self):
        """R² should be 1.0 for perfect fit."""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1, 2, 3, 4, 5])
        r2 = calculate_r2(y_true, y_pred)
        assert r2 == 1.0
    
    def test_no_variation(self):
        """R² should be 0.0 when there's no variation in y_true."""
        y_true = np.array([5, 5, 5, 5])
        y_pred = np.array([1, 2, 3, 4])
        r2 = calculate_r2(y_true, y_pred)
        assert r2 == 0.0
    
    def test_negative_r2(self):
        """R² can be negative for poor fit."""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([5, 4, 3, 2, 1])
        r2 = calculate_r2(y_true, y_pred)
        assert r2 < 0
    
    def test_basic_calculation(self):
        """Basic R² calculation."""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 2.2, 2.8, 4.1, 5.0])
        r2 = calculate_r2(y_true, y_pred)
        assert 0.9 < r2 < 1.0

class TestEmpiricalSurvivalFunction:
    """Tests for empirical survival function calculation."""
    
    def test_basic_sf(self):
        """Basic survival function calculation."""
        data = np.array([1, 2, 3, 4, 5])
        x, s = empirical_survival_function(data)
        
        assert len(x) == len(s)
        assert all(s >= 0) and all(s <= 1)
        # For x=1, P(X>1) = 4/5 = 0.8
        assert abs(s[0] - 0.8) < 0.01
    
    def test_with_x_min(self):
        """Survival function with x_min filter."""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        x, s = empirical_survival_function(data, x_min=5)
        
        # All x values should be >= 5
        assert all(x >= 5)
        # First survival probability should be P(X>5 | X>=5) = 5/6
        assert abs(s[0] - 5/6) < 0.01
    
    def test_empty_data_raises(self):
        """Empty data should raise ValueError."""
        with pytest.raises(ValueError):
            empirical_survival_function(np.array([]))

class TestPlotLoglogSurvival:
    """Tests for log-log survival plot generation."""
    
    def test_basic_plot(self):
        """Basic plot generation."""
        np.random.seed(42)
        data = np.random.gamma(2, 2, 1000)
        
        # Mock fitted distributions
        from scipy import stats
        fitted_dists = {
            'Gamma': {
                'distribution': stats.gamma,
                'params': (2.0, 0.0, 2.0),
                'info': {}
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_plot.png"
            r2, r2_values = plot_loglog_survival(
                data, fitted_dists, output_path=output_path
            )
            
            assert output_path.exists()
            assert isinstance(r2, float)
            assert 'Gamma' in r2_values
    
    def test_multiple_distributions(self):
        """Plot with multiple distributions."""
        np.random.seed(42)
        data = np.random.gamma(2, 2, 1000)
        
        from scipy import stats
        fitted_dists = {
            'Gamma': {
                'distribution': stats.gamma,
                'params': (2.0, 0.0, 2.0),
                'info': {}
            },
            'Weibull': {
                'distribution': stats.weibull_min,
                'params': (2.0, 0.0, 2.0),
                'info': {}
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_plot.png"
            r2, r2_values = plot_loglog_survival(
                data, fitted_dists, output_path=output_path
            )
            
            assert 'Gamma' in r2_values
            assert 'Weibull' in r2_values
            assert len(r2_values) == 2

class TestPlotQQPlot:
    """Tests for Q-Q plot generation."""
    
    def test_basic_qq_plot(self):
        """Basic Q-Q plot generation."""
        np.random.seed(42)
        data = np.random.gamma(2, 2, 1000)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_qq.png"
            plot_qq_plot(
                data, 'Gamma', (2.0, 0.0, 2.0), output_path=output_path
            )
            
            assert output_path.exists()
    
    def test_invalid_distribution(self):
        """Invalid distribution name should raise error."""
        np.random.seed(42)
        data = np.random.gamma(2, 2, 1000)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_qq.png"
            with pytest.raises(ValueError):
                plot_qq_plot(data, 'InvalidDist', (), output_path=output_path)

class TestSaveR2Results:
    """Tests for R² results saving."""
    
    def test_save_r2(self):
        """Test saving R² values to JSON."""
        r2_values = {
            'Gamma': 0.95,
            'Weibull': 0.92,
            'Log-Normal': 0.89
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "r2_results.json"
            save_r2_results(r2_values, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                result = json.load(f)
            
            assert 'r2_values' in result
            assert result['r2_values']['Gamma'] == 0.95
            assert 'visualization only' in result['note']

class TestIntegration:
    """Integration tests for visualization module."""
    
    def test_full_workflow(self):
        """Test full visualization workflow."""
        np.random.seed(42)
        data = np.random.gamma(2, 2, 1000)
        
        from scipy import stats
        fitted_dists = {
            'Gamma': {
                'distribution': stats.gamma,
                'params': (2.0, 0.0, 2.0),
                'info': {}
            },
            'Weibull': {
                'distribution': stats.weibull_min,
                'params': (1.5, 0.0, 2.0),
                'info': {}
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            plot_path = Path(tmpdir) / "plot.png"
            r2_path = Path(tmpdir) / "r2.json"
            
            # Generate plot
            r2, r2_values = plot_loglog_survival(
                data, fitted_dists, output_path=plot_path
            )
            
            # Save R²
            save_r2_results(r2_values, r2_path)
            
            # Verify outputs
            assert plot_path.exists()
            assert r2_path.exists()
            
            # Verify R² values are reasonable
            assert all(0 <= v <= 1 for v in r2_values.values())