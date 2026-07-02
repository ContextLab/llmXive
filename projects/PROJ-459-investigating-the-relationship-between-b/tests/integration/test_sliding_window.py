"""
Integration tests for sliding-window analysis and sensitivity reporting.

Tests verify:
1. Sliding window produces time-series of connectivity matrices.
2. Sensitivity analysis reports ICC values for metric stability.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.atlas import load_atlas, map_to_yeo
from data.models import SensitivityReport
from utils.io import save_json, load_json


class TestSlidingWindowAnalysis:
    """Integration tests for sliding window connectivity computation."""

    @pytest.fixture
    def mock_time_series(self):
        """Generate realistic mock time series for 10 subjects x 400 ROIs x 200 timepoints."""
        np.random.seed(42)
        n_subjects = 10
        n_rois = 400
        n_timepoints = 200
        
        # Generate correlated time series to simulate brain activity
        # Use a simple autoregressive process with added noise
        data = np.zeros((n_subjects, n_rois, n_timepoints))
        
        for s in range(n_subjects):
            for r in range(n_rois):
                # Initialize with random values
                ts = np.random.randn(n_timepoints)
                # Apply autoregressive process (AR(1)) to create temporal correlation
                for t in range(1, n_timepoints):
                    ts[t] = 0.7 * ts[t-1] + 0.3 * np.random.randn()
                data[s, r, :] = ts
        
        return data

    @pytest.fixture
    def mock_network_map(self):
        """Create a mock network mapping for 400 ROIs."""
        # Simulate mapping 400 ROIs to 7 Yeo networks
        np.random.seed(42)
        networks = np.random.choice([1, 2, 3, 4, 5, 6, 7], size=400)
        network_map = {f"roi_{i}": int(networks[i]) for i in range(400)}
        return network_map

    def test_sliding_window_produces_time_series(
        self, 
        mock_time_series, 
        mock_network_map,
        tmp_path
    ):
        """Test that sliding window analysis produces time-series of connectivity matrices."""
        # Import the analysis module
        from analysis.metrics import compute_dynamic_connectivity, compute_reconfiguration_rate
        
        subject_idx = 0
        time_series = mock_time_series[subject_idx]  # Shape: (400, 200)
        
        # Test parameters
        window_size = 30  # TRs
        step_size = 5     # TRs
        
        # Run sliding window analysis
        dynamic_matrices = compute_dynamic_connectivity(
            time_series, 
            window_size=window_size, 
            step=step_size
        )
        
        # Verify output structure
        assert isinstance(dynamic_matrices, list), "Output should be a list of matrices"
        assert len(dynamic_matrices) > 0, "Should produce at least one window"
        
        # Check matrix dimensions
        n_windows = len(dynamic_matrices)
        expected_windows = (200 - window_size) // step_size + 1
        assert n_windows == expected_windows, f"Expected {expected_windows} windows, got {n_windows}"
        
        for matrix in dynamic_matrices:
            assert matrix.shape == (400, 400), f"Each matrix should be 400x400, got {matrix.shape}"
            assert np.allclose(matrix, matrix.T), "Connectivity matrices should be symmetric"
            np.testing.assert_array_almost_equal(
                np.diag(matrix), 
                np.ones(400), 
                decimal=5,
                err_msg="Diagonal should be 1.0 (self-correlation)"
            )
        
        # Test reconfiguration rate calculation
        reconfig_rate = compute_reconfiguration_rate(dynamic_matrices)
        assert isinstance(reconfig_rate, float), "Reconfiguration rate should be a float"
        assert 0 <= reconfig_rate <= 1, f"Reconfiguration rate should be in [0, 1], got {reconfig_rate}"
        
        # Save a sample matrix for verification
        sample_matrix = dynamic_matrices[0]
        output_path = tmp_path / "sample_dynamic_matrix.npy"
        np.save(output_path, sample_matrix)
        assert output_path.exists(), "Sample matrix should be saved to disk"

    def test_sensitivity_analysis_reports_icc(
        self, 
        mock_time_series, 
        mock_network_map,
        tmp_path
    ):
        """Test that sensitivity analysis runs and reports ICC values."""
        from analysis.metrics import run_sensitivity_analysis, compute_icc
        
        subject_idx = 0
        time_series = mock_time_series[subject_idx]
        
        # Test multiple window sizes
        window_sizes = [20, 30, 40]
        
        # Run sensitivity analysis
        sensitivity_results = run_sensitivity_analysis(
            time_series, 
            window_sizes=window_sizes
        )
        
        # Verify output structure
        assert isinstance(sensitivity_results, list), "Sensitivity results should be a list"
        assert len(sensitivity_results) == len(window_sizes), "Should have one result per window size"
        
        # Check each result
        for i, result in enumerate(sensitivity_results):
            assert "window_size" in result, "Result should have window_size"
            assert "icc" in result, "Result should have icc"
            assert "reconfiguration_rate" in result, "Result should have reconfiguration_rate"
            
            assert result["window_size"] == window_sizes[i]
            assert isinstance(result["icc"], float), "ICC should be a float"
            assert -1 <= result["icc"] <= 1, f"ICC should be in [-1, 1], got {result['icc']}"
            assert isinstance(result["reconfiguration_rate"], float)
        
        # Test ICC computation directly with mock data
        mock_metrics = [0.15, 0.18, 0.16, 0.17, 0.19]
        icc_value = compute_icc(mock_metrics)
        assert isinstance(icc_value, float), "ICC should be a float"
        assert -1 <= icc_value <= 1, f"ICC should be in [-1, 1], got {icc_value}"
        
        # Save sensitivity report
        report_path = tmp_path / "sensitivity_report.json"
        report_data = {
            "window_sizes": window_sizes,
            "results": sensitivity_results
        }
        save_json(report_data, report_path)
        
        assert report_path.exists(), "Sensitivity report should be saved"
        
        # Verify we can load it back
        loaded_report = load_json(report_path)
        assert len(loaded_report["results"]) == len(window_sizes)
        assert all("icc" in r for r in loaded_report["results"])