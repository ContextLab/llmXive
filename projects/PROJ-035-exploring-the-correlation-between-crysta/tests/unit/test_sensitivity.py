import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from typing import Dict, Any
from unittest.mock import patch, MagicMock

# Ensure src is in path for imports
src_path = Path(__file__).parent.parent.parent / "code" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.analysis.sensitivity import run_sensitivity_analysis, save_sensitivity_report, setup_logger_module


class TestSensitivityAnalysis:
    """
    Unit tests for sensitivity analysis (T024).
    Verifies p-value sweep output includes results for {0.01, 0.05, 0.1} per FR-009.
    """

    @pytest.fixture
    def mock_stratified_data(self):
        """Create a mock stratified dataset with known correlations."""
        np.random.seed(42)
        n_samples = 100
        
        # Create synthetic but realistic-looking data
        # Octahedral tilting angle (0-15 degrees)
        tilting = np.random.uniform(0, 15, n_samples)
        # Bond length variance (0-0.1 A)
        bond_var = np.random.uniform(0, 0.1, n_samples)
        # Tolerance factor (0.8-1.0)
        tolerance = np.random.uniform(0.8, 1.0, n_samples)
        # Thermal conductivity (random values)
        thermal = np.random.normal(2.0, 0.5, n_samples)
        
        df = pd.DataFrame({
            'chemistry_class': ['oxide'] * n_samples,
            'octahedral_tilting_angle': tilting,
            'bond_length_variance': bond_var,
            'tolerance_factor': tolerance,
            'thermal_conductivity': thermal
        })
        return df

    @pytest.fixture
    def mock_sensitivity_results(self):
        """Expected results structure for validation."""
        return {
            'oxide': {
                'p_value_thresholds': [0.01, 0.05, 0.1],
                'results': [
                    {
                        'threshold': 0.01,
                        'significant_correlations': 0,
                        'total_tests': 0
                    },
                    {
                        'threshold': 0.05,
                        'significant_correlations': 0,
                        'total_tests': 0
                    },
                    {
                        'threshold': 0.1,
                        'significant_correlations': 0,
                        'total_tests': 0
                    }
                ]
            }
        }

    def test_run_sensitivity_analysis_returns_expected_thresholds(self, mock_stratified_data):
        """
        Verify that run_sensitivity_analysis returns results for p-value thresholds
        {0.01, 0.05, 0.1} as required by FR-009.
        """
        # Run the sensitivity analysis
        results = run_sensitivity_analysis(mock_stratified_data)
        
        # Verify the structure exists
        assert isinstance(results, dict), "Results should be a dictionary"
        assert 'oxide' in results, "Results should contain 'oxide' chemistry class"
        
        class_results = results['oxide']
        assert 'p_value_thresholds' in class_results, "Should contain p_value_thresholds"
        assert 'results' in class_results, "Should contain results list"
        
        # Verify the specific thresholds required by FR-009
        thresholds = class_results['p_value_thresholds']
        assert 0.01 in thresholds, "Should include p-value threshold 0.01"
        assert 0.05 in thresholds, "Should include p-value threshold 0.05"
        assert 0.1 in thresholds, "Should include p-value threshold 0.1"
        
        # Verify results list matches thresholds
        result_thresholds = [r['threshold'] for r in class_results['results']]
        assert 0.01 in result_thresholds, "Results should include entry for threshold 0.01"
        assert 0.05 in result_thresholds, "Results should include entry for threshold 0.05"
        assert 0.1 in result_thresholds, "Results should include entry for threshold 0.1"

    def test_sensitivity_results_structure(self, mock_stratified_data):
        """
        Verify that each threshold result has the expected structure.
        """
        results = run_sensitivity_analysis(mock_stratified_data)
        class_results = results['oxide']
        
        for result in class_results['results']:
            assert 'threshold' in result, "Each result should have a threshold"
            assert 'significant_correlations' in result, "Each result should have significant_correlations count"
            assert 'total_tests' in result, "Each result should have total_tests count"
            
            # Verify threshold values are one of the expected ones
            assert result['threshold'] in [0.01, 0.05, 0.1], f"Unexpected threshold: {result['threshold']}"

    def test_save_sensitivity_report_writes_file(self, mock_stratified_data, tmp_path):
        """
        Verify that save_sensitivity_report creates a valid JSON file.
        """
        output_path = tmp_path / "sensitivity_report.json"
        
        # Run analysis and save
        results = run_sensitivity_analysis(mock_stratified_data)
        save_sensitivity_report(results, str(output_path))
        
        # Verify file was created
        assert output_path.exists(), "Report file should be created"
        
        # Verify file is valid JSON
        import json
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert 'oxide' in saved_data, "Saved data should contain 'oxide' class"
        assert 'p_value_thresholds' in saved_data['oxide'], "Saved data should contain thresholds"

    def test_empty_dataframe_handling(self):
        """
        Verify that an empty dataframe is handled gracefully.
        """
        empty_df = pd.DataFrame(columns=[
            'chemistry_class', 'octahedral_tilting_angle', 
            'bond_length_variance', 'tolerance_factor', 'thermal_conductivity'
        ])
        
        # Should not raise an exception, but return empty results
        results = run_sensitivity_analysis(empty_df)
        
        # Verify structure is maintained even if empty
        assert isinstance(results, dict), "Results should be a dictionary"

    def test_multiple_chemistry_classes(self):
        """
        Verify that multiple chemistry classes are handled correctly.
        """
        np.random.seed(42)
        n_samples = 50
        
        # Create data with multiple chemistry classes
        df = pd.DataFrame({
            'chemistry_class': ['oxide'] * n_samples + ['halide'] * n_samples,
            'octahedral_tilting_angle': np.random.uniform(0, 15, 2 * n_samples),
            'bond_length_variance': np.random.uniform(0, 0.1, 2 * n_samples),
            'tolerance_factor': np.random.uniform(0.8, 1.0, 2 * n_samples),
            'thermal_conductivity': np.random.normal(2.0, 0.5, 2 * n_samples)
        })
        
        results = run_sensitivity_analysis(df)
        
        assert 'oxide' in results, "Should contain oxide class"
        assert 'halide' in results, "Should contain halide class"
        
        # Both should have the required thresholds
        for class_name in ['oxide', 'halide']:
            assert 0.01 in results[class_name]['p_value_thresholds']
            assert 0.05 in results[class_name]['p_value_thresholds']
            assert 0.1 in results[class_name]['p_value_thresholds']

    def test_sensitivity_analysis_completeness(self, mock_stratified_data):
        """
        Comprehensive test to ensure the sensitivity analysis is complete
        and meets all FR-009 requirements.
        """
        results = run_sensitivity_analysis(mock_stratified_data)
        
        # Check all required thresholds are present
        required_thresholds = {0.01, 0.05, 0.1}
        for class_name, class_results in results.items():
            present_thresholds = set(class_results['p_value_thresholds'])
            assert present_thresholds == required_thresholds, (
                f"Class {class_name} missing thresholds. Expected {required_thresholds}, got {present_thresholds}"
            )
            
            # Check that results list has exactly 3 entries (one per threshold)
            assert len(class_results['results']) == 3, (
                f"Class {class_name} should have exactly 3 results, got {len(class_results['results'])}"
            )
            
            # Verify each result entry
            for res in class_results['results']:
                assert res['threshold'] in required_thresholds
                assert isinstance(res['significant_correlations'], int)
                assert isinstance(res['total_tests'], int)
                assert res['total_tests'] >= 0
                assert res['significant_correlations'] >= 0
                assert res['significant_correlations'] <= res['total_tests']