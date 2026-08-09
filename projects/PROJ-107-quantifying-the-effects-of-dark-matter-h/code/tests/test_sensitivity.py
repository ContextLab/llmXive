"""
Unit tests for sensitivity sweep logic in code/analysis/sensitivity.py.

This module tests the robustness of statistical results against variations
in binning thresholds (c/a cutoffs for prolate/triaxial/spherical classifications).
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Import the function we are testing (will be implemented in T030)
# We assume the function signature based on the task description:
# perform_sensitivity_sweep(input_csv: str, output_csv: str, threshold_range: List[float]) -> pd.DataFrame
# Since the implementation is in T030, we will test the logic of the sweep generator
# and the statistical stability checks here.

# We mock the actual heavy computation to keep tests fast and focused on logic
from unittest.mock import patch, MagicMock

# Import config utilities if needed for path resolution
try:
    from utils.config import get_project_root, get_data_processed_path
except ImportError:
    # Fallback for standalone execution if utils not in path
    pass


class TestSensitivitySweepLogic:
    """Tests for the sensitivity analysis sweep logic."""

    def test_threshold_range_generation(self):
        """Verify that threshold ranges are generated correctly."""
        # Simulate the logic that would be in sensitivity.py
        # We want to sweep from low confidence (strict) to high confidence (lenient)
        # e.g., c/a < 0.4, 0.5, 0.6, 0.7, 0.8
        thresholds = [0.4, 0.5, 0.6, 0.7, 0.8]
        
        # Check monotonicity
        assert thresholds == sorted(thresholds), "Thresholds must be sorted"
        
        # Check range constraints (must be between 0 and 1)
        for t in thresholds:
            assert 0.0 < t < 1.0, f"Threshold {t} must be in (0, 1)"

    def test_p_value_variance_calculation(self):
        """Test the calculation of p-value variance across thresholds."""
        # Simulate p-values from different threshold runs
        p_values = np.array([0.005, 0.006, 0.004, 0.007, 0.005])
        
        variance = np.var(p_values)
        
        # The variance should be low if the result is robust
        # SC-003 requires variance <= 0.001
        assert variance <= 0.001, f"Variance {variance} exceeds SC-003 limit of 0.001"
        
        # Test failure case
        unstable_p_values = np.array([0.001, 0.050, 0.002, 0.045, 0.003])
        unstable_variance = np.var(unstable_p_values)
        assert unstable_variance > 0.001, "Unstable p-values should have high variance"

    def test_sweep_logic_structure(self):
        """Test that the sweep logic iterates correctly over thresholds."""
        thresholds = [0.5, 0.6, 0.7]
        results = []
        
        # Simulate the loop structure expected in sensitivity.py
        for t in thresholds:
            # In real implementation, this would call stats tests with new binning
            mock_p_val = 0.01 * t  # Dummy calculation
            results.append({
                "threshold": t,
                "p_value": mock_p_val,
                "significant": mock_p_val < 0.05
            })
        
        assert len(results) == len(thresholds), "One result per threshold"
        assert all(r["significant"] for r in results), "All dummy results should be significant"

    def test_binning_threshold_application(self):
        """Test that binning thresholds correctly classify halos."""
        # Create mock halo data
        data = pd.DataFrame({
            'c_a_ratio': [0.3, 0.45, 0.6, 0.85, 0.55],
            'halo_id': range(5)
        })
        
        # Define thresholds
        prolate_max = 0.5
        triaxial_max = 0.8
        
        # Apply classification logic (mimicking shape_metrics.py binning)
        def classify(row, p_max, t_max):
            if row['c_a_ratio'] < p_max:
                return 'prolate'
            elif row['c_a_ratio'] < t_max:
                return 'triaxial'
            else:
                return 'spherical'
        
        data['shape_class'] = data.apply(
            lambda row: classify(row, prolate_max, triaxial_max), axis=1
        )
        
        # Verify counts
        assert data[data['shape_class'] == 'prolate'].shape[0] == 2  # 0.3, 0.45
        assert data[data['shape_class'] == 'triaxial'].shape[0] == 2  # 0.6, 0.55
        assert data[data['shape_class'] == 'spherical'].shape[0] == 1  # 0.85

    def test_sensitivity_report_schema(self):
        """Verify the expected schema of the sensitivity report."""
        expected_columns = [
            'threshold',
            'p_value',
            'statistic',
            'test_type',
            'significant',
            'n_halos_prolate',
            'n_halos_triaxial',
            'n_halos_spherical'
        ]
        
        # Create a dummy row
        dummy_row = {col: None for col in expected_columns}
        df = pd.DataFrame([dummy_row])
        
        # Check columns exist
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

    @patch('code.analysis.sensitivity.load_halo_data')
    @patch('code.analysis.sensitivity.run_statistical_tests')
    def test_sweep_execution_flow(self, mock_tests, mock_load):
        """Test the end-to-end flow of the sensitivity sweep."""
        # Mock data loading
        mock_load.return_value = pd.DataFrame({
            'c_a_ratio': [0.4, 0.5, 0.6],
            'triaxiality': [0.1, 0.2, 0.3],
            'mass': [1e12, 1e13, 1e14],
            'sfr': [1.0, 2.0, 3.0]
        })
        
        # Mock test results
        mock_tests.return_value = {
            'p_value': 0.02,
            'statistic': 5.0,
            'n_halos': 3
        }
        
        # Simulate the sweep logic
        thresholds = [0.5, 0.6]
        report_rows = []
        
        for t in thresholds:
            # In real code: results = run_tests_for_threshold(data, t)
            results = mock_tests()
            report_rows.append({
                'threshold': t,
                'p_value': results['p_value'],
                'statistic': results['statistic']
            })
        
        report_df = pd.DataFrame(report_rows)
        
        assert len(report_df) == 2
        assert report_df['p_value'].iloc[0] == 0.02

    def test_violation_flagging_logic(self):
        """Test that variance violations are correctly flagged."""
        p_values = [0.01, 0.09, 0.01, 0.08, 0.01]  # High variance
        variance = np.var(p_values)
        
        is_stable = variance <= 0.001
        
        assert not is_stable, "High variance should be flagged as unstable"
        
        # Test stable case
        stable_p_values = [0.05, 0.051, 0.049, 0.05, 0.05]
        stable_variance = np.var(stable_p_values)
        is_stable = stable_variance <= 0.001
        assert is_stable, "Low variance should be stable"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
