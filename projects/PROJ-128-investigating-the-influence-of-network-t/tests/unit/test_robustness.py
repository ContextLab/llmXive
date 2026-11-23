"""
Unit tests for sensitivity analysis logic in code/analysis/robustness.py.

This module validates the robustness analysis pipeline, specifically:
1. Loading processed metrics from CSV files.
2. Recomputing graph metrics for different density thresholds.
3. Calculating sensitivity metrics (absolute differences).
4. Verifying the structure of sensitivity results.

These tests ensure that the sensitivity analysis logic correctly identifies
how structural and functional metrics change with parameter variations,
satisfying FR-008 (Graph Density Sensitivity) and Constitution Principle VII
(20 TR Validation).
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add the project root to the path so we can import code modules
# In a real execution environment, this would be handled by PYTHONPATH
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.robustness import (
    load_processed_metrics,
    recompute_graph_metrics_for_density,
    calculate_sensitivity_metrics,
    run_sensitivity_analysis,
    save_sensitivity_results
)
from config import get_config_dict


class TestLoadProcessedMetrics:
    """Tests for the load_processed_metrics function."""

    def test_load_structural_metrics(self, tmp_path):
        """Test loading structural metrics CSV."""
        # Create a mock structural metrics file
        mock_data = {
            'subject_id': ['001', '002', '003'],
            'global_efficiency': [0.45, 0.52, 0.48],
            'clustering_coefficient': [0.35, 0.42, 0.38],
            'modularity': [0.65, 0.71, 0.68],
            'density': [0.15, 0.15, 0.15]
        }
        df = pd.DataFrame(mock_data)
        mock_file = tmp_path / "structural_metrics.csv"
        df.to_csv(mock_file, index=False)

        # Load and verify
        result = load_processed_metrics(str(mock_file))
        
        assert result is not None
        assert len(result) == 3
        assert 'subject_id' in result.columns
        assert 'global_efficiency' in result.columns
        assert 'clustering_coefficient' in result.columns
        assert 'modularity' in result.columns
        assert list(result['subject_id']) == ['001', '002', '003']

    def test_load_missing_file(self, tmp_path):
        """Test handling of missing file."""
        non_existent = tmp_path / "non_existent.csv"
        
        with pytest.raises(FileNotFoundError):
            load_processed_metrics(str(non_existent))

    def test_load_correlation_results(self, tmp_path):
        """Test loading correlation results CSV."""
        mock_data = {
            'structural_metric': ['global_efficiency', 'clustering_coefficient'],
            'functional_metric': ['mean_dwell_time', 'num_visits'],
            'r_value': [0.45, -0.32],
            'p_value': [0.01, 0.04],
            'fdr_corrected': [True, False]
        }
        df = pd.DataFrame(mock_data)
        mock_file = tmp_path / "correlation_results.csv"
        df.to_csv(mock_file, index=False)

        result = load_processed_metrics(str(mock_file))
        
        assert result is not None
        assert len(result) == 2
        assert 'r_value' in result.columns
        assert 'p_value' in result.columns


class TestRecomputeGraphMetricsForDensity:
    """Tests for the recompute_graph_metrics_for_density function."""

    def test_recompute_metrics_varies_with_density(self):
        """
        Test that graph metrics change when density threshold changes.
        
        This validates the core assumption of FR-008: that graph topology
        is sensitive to density thresholding.
        """
        # Create a mock adjacency matrix
        np.random.seed(42)
        n_nodes = 20
        adj_matrix = np.random.rand(n_nodes, n_nodes)
        np.fill_diagonal(adj_matrix, 0)

        # Compute metrics at different densities
        metrics_low = recompute_graph_metrics_for_density(adj_matrix, 0.10)
        metrics_high = recompute_graph_metrics_for_density(adj_matrix, 0.20)

        # Metrics should differ
        assert metrics_low['global_efficiency'] != metrics_high['global_efficiency']
        assert metrics_low['clustering_coefficient'] != metrics_high['clustering_coefficient']

        # Verify structure
        for key in ['global_efficiency', 'clustering_coefficient', 'modularity']:
            assert key in metrics_low
            assert key in metrics_high

    def test_recompute_metrics_handles_edge_cases(self):
        """Test handling of extreme density thresholds."""
        np.random.seed(42)
        n_nodes = 10
        adj_matrix = np.random.rand(n_nodes, n_nodes)
        np.fill_diagonal(adj_matrix, 0)

        # Very low density (almost no edges)
        metrics_very_low = recompute_graph_metrics_for_density(adj_matrix, 0.01)
        
        # Very high density (almost all edges)
        metrics_very_high = recompute_graph_metrics_for_density(adj_matrix, 0.99)

        # Both should return valid metrics (though potentially extreme)
        assert isinstance(metrics_very_low, dict)
        assert isinstance(metrics_very_high, dict)

        # Very high density should have higher global efficiency
        assert metrics_very_high['global_efficiency'] >= metrics_very_low['global_efficiency']

    def test_recompute_metrics_uses_config_thresholds(self):
        """Test that the function respects config density thresholds."""
        config = get_config_dict()
        thresholds = config.get('DENSITY_THRESHOLD_VARIATIONS', [0.10, 0.15, 0.20])
        
        np.random.seed(42)
        n_nodes = 15
        adj_matrix = np.random.rand(n_nodes, n_nodes)
        np.fill_diagonal(adj_matrix, 0)

        # Test each threshold
        for threshold in thresholds:
            metrics = recompute_graph_metrics_for_density(adj_matrix, threshold)
            assert metrics is not None
            assert 'global_efficiency' in metrics


class TestCalculateSensitivityMetrics:
    """Tests for the calculate_sensitivity_metrics function."""

    def test_calculate_absolute_difference(self):
        """Test calculation of absolute differences between conditions."""
        # Mock baseline and validation metrics
        baseline_metrics = {
            'global_efficiency': 0.45,
            'clustering_coefficient': 0.35,
            'modularity': 0.65
        }
        
        validation_metrics = {
            'global_efficiency': 0.42,
            'clustering_coefficient': 0.38,
            'modularity': 0.63
        }

        result = calculate_sensitivity_metrics(baseline_metrics, validation_metrics)

        # Check that absolute differences are calculated
        assert 'global_efficiency_diff' in result
        assert 'clustering_coefficient_diff' in result
        assert 'modularity_diff' in result

        # Verify values
        assert result['global_efficiency_diff'] == abs(0.45 - 0.42)
        assert result['clustering_coefficient_diff'] == abs(0.35 - 0.38)
        assert result['modularity_diff'] == abs(0.65 - 0.63)

    def test_calculate_sensitivity_handles_missing_keys(self):
        """Test handling of missing metric keys."""
        baseline_metrics = {
            'global_efficiency': 0.45,
            'clustering_coefficient': 0.35
        }
        
        validation_metrics = {
            'global_efficiency': 0.42,
            'modularity': 0.63  # Missing clustering_coefficient
        }

        result = calculate_sensitivity_metrics(baseline_metrics, validation_metrics)

        # Should handle missing keys gracefully
        assert 'global_efficiency_diff' in result
        # clustering_coefficient_diff might be None or missing
        assert 'modularity_diff' in result

    def test_calculate_sensitivity_with_correlation_results(self):
        """Test sensitivity calculation for correlation coefficients."""
        # Mock correlation results
        baseline_corr = {
            ('global_efficiency', 'mean_dwell_time'): 0.45,
            ('clustering_coefficient', 'num_visits'): -0.32
        }
        
        validation_corr = {
            ('global_efficiency', 'mean_dwell_time'): 0.41,
            ('clustering_coefficient', 'num_visits'): -0.35
        }

        result = calculate_sensitivity_metrics(baseline_corr, validation_corr)

        # Check that absolute differences are calculated for correlations
        assert ('global_efficiency', 'mean_dwell_time') in result
        assert ('clustering_coefficient', 'num_visits') in result

        # Verify values
        assert result[('global_efficiency', 'mean_dwell_time')] == abs(0.45 - 0.41)
        assert result[('clustering_coefficient', 'num_visits')] == abs(-0.32 - (-0.35))

    def test_calculate_sensitivity_returns_dict(self):
        """Test that the function returns a dictionary."""
        baseline = {'metric_a': 1.0, 'metric_b': 2.0}
        validation = {'metric_a': 1.2, 'metric_b': 1.8}

        result = calculate_sensitivity_metrics(baseline, validation)

        assert isinstance(result, dict)
        assert len(result) == 2


class TestRunSensitivityAnalysis:
    """Tests for the run_sensitivity_analysis function."""

    def test_run_sensitivity_analysis_full_pipeline(self, tmp_path):
        """Test the full sensitivity analysis pipeline."""
        # Create mock data
        config = get_config_dict()
        density_thresholds = config.get('DENSITY_THRESHOLD_VARIATIONS', [0.10, 0.15, 0.20])

        # Create a mock structural metrics file
        mock_structural = pd.DataFrame({
            'subject_id': ['001', '002'],
            'global_efficiency': [0.45, 0.52],
            'clustering_coefficient': [0.35, 0.42],
            'modularity': [0.65, 0.71],
            'density': [0.15, 0.15]
        })
        structural_file = tmp_path / "structural_metrics.csv"
        mock_structural.to_csv(structural_file, index=False)

        # Run sensitivity analysis
        results = run_sensitivity_analysis(
            structural_metrics_path=str(structural_file),
            density_thresholds=density_thresholds
        )

        # Verify results structure
        assert results is not None
        assert isinstance(results, dict)
        assert 'sensitivity_results' in results
        assert 'summary' in results

        # Check that sensitivity results contain expected keys
        sensitivity_results = results['sensitivity_results']
        for threshold in density_thresholds:
            assert str(threshold) in sensitivity_results

    def test_run_sensitivity_analysis_handles_empty_data(self, tmp_path):
        """Test handling of empty input data."""
        mock_structural = pd.DataFrame({
            'subject_id': [],
            'global_efficiency': [],
            'clustering_coefficient': [],
            'modularity': [],
            'density': []
        })
        structural_file = tmp_path / "structural_metrics.csv"
        mock_structural.to_csv(structural_file, index=False)

        # Should handle empty data gracefully
        results = run_sensitivity_analysis(
            structural_metrics_path=str(structural_file),
            density_thresholds=[0.10, 0.15, 0.20]
        )

        assert results is not None
        assert 'sensitivity_results' in results

    def test_run_sensitivity_analysis_with_correlation_data(self, tmp_path):
        """Test sensitivity analysis with correlation results."""
        # Create mock correlation results
        mock_correlation = pd.DataFrame({
            'structural_metric': ['global_efficiency', 'clustering_coefficient'],
            'functional_metric': ['mean_dwell_time', 'num_visits'],
            'r_value': [0.45, -0.32],
            'p_value': [0.01, 0.04],
            'fdr_corrected': [True, False]
        })
        correlation_file = tmp_path / "correlation_results.csv"
        mock_correlation.to_csv(correlation_file, index=False)

        # Run sensitivity analysis on correlation data
        results = run_sensitivity_analysis(
            structural_metrics_path=str(correlation_file),
            density_thresholds=[0.10, 0.15, 0.20],
            is_correlation_data=True
        )

        assert results is not None
        assert 'sensitivity_results' in results


class TestSaveSensitivityResults:
    """Tests for the save_sensitivity_results function."""

    def test_save_sensitivity_results_creates_file(self, tmp_path):
        """Test that the function creates the output file."""
        mock_results = {
            'sensitivity_results': {
                '0.10': {'global_efficiency_diff': 0.03},
                '0.15': {'global_efficiency_diff': 0.02},
                '0.20': {'global_efficiency_diff': 0.01}
            },
            'summary': {
                'max_diff': 0.03,
                'min_diff': 0.01,
                'mean_diff': 0.02
            }
        }

        output_file = tmp_path / "sensitivity_analysis_results.json"
        save_sensitivity_results(mock_results, str(output_file))

        assert output_file.exists()

        # Verify file contents
        with open(output_file, 'r') as f:
            loaded_results = json.load(f)

        assert loaded_results == mock_results

    def test_save_sensitivity_results_invalid_path(self, tmp_path):
        """Test handling of invalid output path."""
        mock_results = {'test': 'data'}
        invalid_path = tmp_path / "nonexistent_dir" / "results.json"

        with pytest.raises(OSError):
            save_sensitivity_results(mock_results, str(invalid_path))

    def test_save_sensitivity_results_format(self, tmp_path):
        """Test that the saved file has the correct format."""
        mock_results = {
            'sensitivity_results': {
                '0.10': {'metric_a': 0.01, 'metric_b': 0.02},
                '0.15': {'metric_a': 0.015, 'metric_b': 0.025},
                '0.20': {'metric_a': 0.02, 'metric_b': 0.03}
            },
            'summary': {
                'total_comparisons': 6,
                'max_sensitivity': 0.03
            }
        }

        output_file = tmp_path / "sensitivity_analysis_results.json"
        save_sensitivity_results(mock_results, str(output_file))

        with open(output_file, 'r') as f:
            loaded_results = json.load(f)

        # Verify structure
        assert 'sensitivity_results' in loaded_results
        assert 'summary' in loaded_results
        assert len(loaded_results['sensitivity_results']) == 3


class TestIntegrationSensitivityAnalysis:
    """Integration tests for the complete sensitivity analysis workflow."""

    def test_end_to_end_sensitivity_workflow(self, tmp_path):
        """Test the complete workflow from data loading to result saving."""
        # Setup
        config = get_config_dict()
        density_thresholds = config.get('DENSITY_THRESHOLD_VARIATIONS', [0.10, 0.15, 0.20])

        # Create mock structural metrics
        mock_data = {
            'subject_id': [f'{i:03d}' for i in range(1, 6)],
            'global_efficiency': np.random.rand(5) * 0.2 + 0.3,
            'clustering_coefficient': np.random.rand(5) * 0.2 + 0.2,
            'modularity': np.random.rand(5) * 0.2 + 0.5,
            'density': [0.15] * 5
        }
        df = pd.DataFrame(mock_data)
        structural_file = tmp_path / "structural_metrics.csv"
        df.to_csv(structural_file, index=False)

        # Run full pipeline
        results = run_sensitivity_analysis(
            structural_metrics_path=str(structural_file),
            density_thresholds=density_thresholds
        )

        # Save results
        output_file = tmp_path / "sensitivity_results.json"
        save_sensitivity_results(results, str(output_file))

        # Verify output
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_results = json.load(f)

        # Validate structure
        assert 'sensitivity_results' in saved_results
        assert 'summary' in saved_results
        
        # Check that all thresholds are represented
        for threshold in density_thresholds:
            assert str(threshold) in saved_results['sensitivity_results']

    def test_sensitivity_analysis_identifies_stable_metrics(self, tmp_path):
        """Test that the analysis can identify metrics that are stable across thresholds."""
        # Create data where one metric is stable and another is sensitive
        mock_data = {
            'subject_id': ['001', '002', '003'],
            'global_efficiency': [0.45, 0.52, 0.48],  # Sensitive
            'clustering_coefficient': [0.35, 0.35, 0.35],  # Stable
            'modularity': [0.65, 0.71, 0.68],
            'density': [0.15, 0.15, 0.15]
        }
        df = pd.DataFrame(mock_data)
        structural_file = tmp_path / "structural_metrics.csv"
        df.to_csv(structural_file, index=False)

        results = run_sensitivity_analysis(
            structural_metrics_path=str(structural_file),
            density_thresholds=[0.10, 0.15, 0.20]
        )

        # The summary should indicate which metrics are most/least sensitive
        assert 'summary' in results
        assert 'max_diff' in results['summary']
        assert 'min_diff' in results['summary']

    def test_sensitivity_analysis_handles_correlation_stability(self, tmp_path):
        """Test sensitivity analysis for correlation coefficient stability."""
        # Create mock correlation results
        mock_data = {
            'structural_metric': ['global_efficiency', 'clustering_coefficient'],
            'functional_metric': ['mean_dwell_time', 'num_visits'],
            'r_value': [0.45, -0.32],
            'p_value': [0.01, 0.04],
            'fdr_corrected': [True, False]
        }
        df = pd.DataFrame(mock_data)
        correlation_file = tmp_path / "correlation_results.csv"
        df.to_csv(correlation_file, index=False)

        # Run sensitivity analysis
        results = run_sensitivity_analysis(
            structural_metrics_path=str(correlation_file),
            density_thresholds=[0.10, 0.15, 0.20],
            is_correlation_data=True
        )

        assert results is not None
        assert 'sensitivity_results' in results


if __name__ == '__main__':
    pytest.main([__file__, '-v'])