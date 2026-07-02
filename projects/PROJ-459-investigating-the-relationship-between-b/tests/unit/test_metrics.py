"""
Unit tests for network metrics computation.
"""
import pytest
import numpy as np
from code.analysis.metrics import (
    compute_static_connectivity,
    compute_static_metrics,
    compute_dynamic_connectivity,
    compute_reconfiguration_rate,
    regress_confounds,
    run_sensitivity_analysis,
    compute_icc
)
from code.utils.atlas import get_roi_networks

class TestStaticConnectivity:
    def test_compute_static_connectivity_shape(self):
        """Test that correlation matrix has correct shape."""
        n_timepoints = 100
        n_rois = 50
        time_series = np.random.randn(n_timepoints, n_rois)
        
        matrix = compute_static_connectivity(time_series)
        
        assert matrix.shape == (n_rois, n_rois)
        assert np.allclose(matrix, matrix.T)  # Symmetric
    
    def test_compute_static_connectivity_diagonal(self):
        """Test that diagonal is all ones."""
        time_series = np.random.randn(100, 20)
        matrix = compute_static_connectivity(time_series)
        
        assert np.allclose(np.diag(matrix), 1.0)
    
    def test_compute_static_connectivity_invalid_input(self):
        """Test error handling for invalid input."""
        with pytest.raises(ValueError):
            compute_static_connectivity(np.random.randn(100))  # 1D array
        
        with pytest.raises(ValueError):
            compute_static_connectivity(np.random.randn(1, 10))  # Only 1 timepoint
    
    def test_compute_static_connectivity_nan_handling(self):
        """Test that NaN values are handled."""
        time_series = np.random.randn(100, 20)
        time_series[0, 0] = np.nan
        
        matrix = compute_static_connectivity(time_series)
        
        # Should not raise, but may contain NaN or be replaced
        assert matrix.shape == (20, 20)

class TestStaticMetrics:
    def test_compute_static_metrics_returns_list(self):
        """Test that metrics function returns a list."""
        matrix = np.random.randn(50, 50)
        network_map = get_roi_networks()
        
        metrics = compute_static_metrics(matrix, network_map)
        
        assert isinstance(metrics, list)
        assert len(metrics) > 0
    
    def test_compute_static_metrics_global_efficiency(self):
        """Test that global efficiency is computed."""
        matrix = np.random.randn(50, 50)
        network_map = get_roi_networks()
        
        metrics = compute_static_metrics(matrix, network_map)
        
        metric_names = [m.metric_name for m in metrics]
        assert "global_efficiency" in metric_names
    
    def test_compute_static_metrics_modularity(self):
        """Test that modularity is computed."""
        matrix = np.random.randn(50, 50)
        network_map = get_roi_networks()
        
        metrics = compute_static_metrics(matrix, network_map)
        
        metric_names = [m.metric_name for m in metrics]
        assert "modularity_Q" in metric_names
    
    def test_compute_static_metrics_within_module_degree(self):
        """Test that within-module degree is computed for networks."""
        matrix = np.random.randn(50, 20)  # Smaller for speed
        network_map = get_roi_networks()
        
        metrics = compute_static_metrics(matrix, network_map)
        
        metric_names = [m.metric_name for m in metrics]
        # Should have at least one within-module degree metric
        within_module_metrics = [n for n in metric_names if "within_module_degree" in n]
        assert len(within_module_metrics) > 0

class TestDynamicConnectivity:
    def test_compute_dynamic_connectivity_shape(self):
        """Test that dynamic connectivity returns list of matrices."""
        time_series = np.random.randn(200, 30)
        
        matrices = compute_dynamic_connectivity(time_series, window_size=30, step=5)
        
        assert isinstance(matrices, list)
        assert len(matrices) > 0
        
        # Each matrix should be square
        for mat in matrices:
            assert mat.shape[0] == mat.shape[1]
    
    def test_compute_dynamic_connectivity_window_size(self):
        """Test that window size affects number of matrices."""
        time_series = np.random.randn(200, 30)
        
        matrices_small = compute_dynamic_connectivity(time_series, window_size=20, step=5)
        matrices_large = compute_dynamic_connectivity(time_series, window_size=50, step=5)
        
        # Smaller window should produce more matrices
        assert len(matrices_small) >= len(matrices_large)
    
    def test_compute_dynamic_connectivity_invalid_window(self):
        """Test error handling for invalid window size."""
        time_series = np.random.randn(100, 30)
        
        with pytest.raises(ValueError):
            compute_dynamic_connectivity(time_series, window_size=100)  # Equal to timepoints
        
        with pytest.raises(ValueError):
            compute_dynamic_connectivity(time_series, window_size=30, step=0)

class TestReconfigurationRate:
    def test_compute_reconfiguration_rate_single_window(self):
        """Test rate with single window returns 0."""
        matrices = [np.random.randn(10, 10)]
        
        rate = compute_reconfiguration_rate(matrices)
        
        assert rate == 0.0
    
    def test_compute_reconfiguration_rate_multiple_windows(self):
        """Test rate with multiple windows."""
        matrices = [np.random.randn(10, 10) for _ in range(5)]
        
        rate = compute_reconfiguration_rate(matrices)
        
        assert 0.0 <= rate <= 2.0  # Normalized change should be bounded

class TestConfoundRegression:
    def test_regress_confounds_shape(self):
        """Test that regression preserves shape."""
        time_series = np.random.randn(100, 20)
        confounds = np.random.randn(100, 3)
        
        residuals = regress_confounds(time_series, confounds)
        
        assert residuals.shape == time_series.shape
    
    def test_regress_confounds_invalid_input(self):
        """Test error handling for mismatched dimensions."""
        time_series = np.random.randn(100, 20)
        confounds = np.random.randn(50, 3)  # Wrong number of timepoints
        
        with pytest.raises(ValueError):
            regress_confounds(time_series, confounds)

class TestSensitivityAnalysis:
    def test_run_sensitivity_analysis_returns_dict(self):
        """Test that sensitivity analysis returns dictionary."""
        time_series = np.random.randn(200, 30)
        
        results = run_sensitivity_analysis(time_series, window_sizes=[20, 30, 40])
        
        assert isinstance(results, dict)
        assert "window_20" in results
        assert "window_30" in results
        assert "window_40" in results

class TestICC:
    def test_compute_icc_single_value(self):
        """Test ICC with single value returns 0."""
        rate = compute_icc([0.5])
        assert rate == 0.0
    
    def test_compute_icc_empty_list(self):
        """Test ICC with empty list returns 0."""
        rate = compute_icc([])
        assert rate == 0.0
    
    def test_compute_icc_two_values(self):
        """Test ICC with two values."""
        rate = compute_icc([0.5, 0.6])
        assert 0.0 <= rate <= 1.0
    
    def test_compute_icc_multiple_values(self):
        """Test ICC with multiple values."""
        rate = compute_icc([0.5, 0.55, 0.6, 0.65, 0.7])
        assert 0.0 <= rate <= 1.0