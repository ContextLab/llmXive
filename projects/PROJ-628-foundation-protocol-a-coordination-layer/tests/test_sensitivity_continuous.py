"""
Unit tests for T020b: Sensitivity analysis sweep for continuous metrics.

Tests verify:
1. Cohen's d calculation correctness
2. Paired t-test integration
3. Sensitivity sweep logic
4. CSV output format compliance
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from experiments.run_sensitivity_continuous import (
    calculate_cohen_d,
    run_sensitivity_sweep,
    save_results,
    check_prerequisites,
    ALPHA_LEVELS,
    CONTINUOUS_METRICS
)
from experiments.stats_analyzer import run_paired_ttest


class TestCohenD:
    """Tests for Cohen's d calculation."""

    def test_cohen_d_identical_groups(self):
        """Cohen's d should be 0 for identical groups."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [1.0, 2.0, 3.0, 4.0, 5.0]
        d = calculate_cohen_d(group1, group2)
        assert d == 0.0

    def test_cohen_d_large_effect(self):
        """Test large effect size."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [10.0, 11.0, 12.0, 13.0, 14.0]
        d = calculate_cohen_d(group1, group2)
        # Large difference should yield large Cohen's d
        assert abs(d) > 2.0

    def test_cohen_d_small_effect(self):
        """Test small effect size."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [1.1, 2.1, 3.1, 4.1, 5.1]
        d = calculate_cohen_d(group1, group2)
        # Small difference should yield small Cohen's d
        assert abs(d) < 0.5

    def test_cohen_d_single_element(self):
        """Should handle single element gracefully (return 0)."""
        group1 = [1.0]
        group2 = [2.0]
        d = calculate_cohen_d(group1, group2)
        assert d == 0.0

    def test_cohen_d_empty_groups(self):
        """Should handle empty groups gracefully (return 0)."""
        d = calculate_cohen_d([], [])
        assert d == 0.0

    def test_cohen_d_zero_variance(self):
        """Should handle zero variance gracefully."""
        group1 = [5.0, 5.0, 5.0]
        group2 = [5.0, 5.0, 5.0]
        d = calculate_cohen_d(group1, group2)
        assert d == 0.0


class TestSensitivitySweep:
    """Tests for the sensitivity sweep logic."""

    @pytest.fixture
    def mock_experiment_data(self):
        """Create mock experiment data."""
        data = []
        # Generate 30 seeds worth of mock data
        for seed in range(30):
            # Foundation protocol (lower values expected)
            data.append({
                'protocol': 'foundation',
                'seed': seed,
                'episode_length': 80 + np.random.normal(0, 5),
                'messages': 40 + np.random.normal(0, 3),
                'bandwidth': 1000 + np.random.normal(0, 100),
                'latency': 50 + np.random.normal(0, 5)
            })
            # Native direct protocol (higher values)
            data.append({
                'protocol': 'native_direct',
                'seed': seed,
                'episode_length': 90 + np.random.normal(0, 5),
                'messages': 50 + np.random.normal(0, 3),
                'bandwidth': 1200 + np.random.normal(0, 100),
                'latency': 60 + np.random.normal(0, 5)
            })
        return data

    def test_run_sensitivity_sweep_structure(self, mock_experiment_data):
        """Test that the sweep returns correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            results_file = data_dir / "simulation_results.json"
            
            with open(results_file, 'w') as f:
                json.dump(mock_experiment_data, f)
            
            results = run_sensitivity_sweep(data_dir)
            
            assert isinstance(results, list)
            assert len(results) > 0
            
            # Check each result has required keys
            for r in results:
                assert 'alpha' in r
                assert 'metric' in r
                assert 'p_value' in r
                assert 'cohen_d' in r
                assert 'significant' in r

    def test_run_sensitivity_sweep_alpha_coverage(self, mock_experiment_data):
        """Test that all alpha levels are covered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            results_file = data_dir / "simulation_results.json"
            
            with open(results_file, 'w') as f:
                json.dump(mock_experiment_data, f)
            
            results = run_sensitivity_sweep(data_dir)
            
            # Extract all unique alpha values
            alphas = sorted(set(r['alpha'] for r in results))
            
            # Should cover all defined alpha levels
            for alpha in ALPHA_LEVELS:
                assert alpha in alphas

    def test_run_sensitivity_sweep_metric_coverage(self, mock_experiment_data):
        """Test that all continuous metrics are covered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            results_file = data_dir / "simulation_results.json"
            
            with open(results_file, 'w') as f:
                json.dump(mock_experiment_data, f)
            
            results = run_sensitivity_sweep(data_dir)
            
            # Extract all unique metrics
            metrics = set(r['metric'] for r in results)
            
            # Should cover all defined continuous metrics
            for metric in CONTINUOUS_METRICS:
                assert metric in metrics

    def test_run_sensitivity_sweep_significance_logic(self, mock_experiment_data):
        """Test that significance logic is correct (lower alpha = fewer significant)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            results_file = data_dir / "simulation_results.json"
            
            with open(results_file, 'w') as f:
                json.dump(mock_experiment_data, f)
            
            results = run_sensitivity_sweep(data_dir)
            
            # Group by metric
            for metric in CONTINUOUS_METRICS:
                metric_results = [r for r in results if r['metric'] == metric]
                
                # Count significant at different alpha levels
                sig_at_001 = sum(1 for r in metric_results if r['alpha'] == 0.001 and r['significant'])
                sig_at_05 = sum(1 for r in metric_results if r['alpha'] == 0.05 and r['significant'])
                sig_at_20 = sum(1 for r in metric_results if r['alpha'] == 0.20 and r['significant'])
                
                # As alpha increases, significance count should not decrease
                assert sig_at_001 <= sig_at_05 <= sig_at_20


class TestSaveResults:
    """Tests for saving results to CSV."""

    def test_save_results_creates_file(self):
        """Test that save_results creates the output file."""
        results = [
            {'alpha': 0.05, 'metric': 'episode_length', 'p_value': 0.03, 'cohen_d': 0.5, 'significant': True}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            
            success = save_results(results, output_path)
            
            assert success
            assert output_path.exists()

    def test_save_results_csv_format(self):
        """Test that the CSV has correct columns."""
        results = [
            {'alpha': 0.05, 'metric': 'episode_length', 'p_value': 0.03, 'cohen_d': 0.5, 'significant': True},
            {'alpha': 0.01, 'metric': 'messages', 'p_value': 0.005, 'cohen_d': 0.8, 'significant': True}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            
            save_results(results, output_path)
            
            df = pd.read_csv(output_path)
            
            # Check columns
            expected_columns = ['alpha', 'metric', 'p_value', 'cohen_d', 'significant']
            assert list(df.columns) == expected_columns

    def test_save_results_data_integrity(self):
        """Test that data is saved correctly."""
        results = [
            {'alpha': 0.05, 'metric': 'episode_length', 'p_value': 0.03, 'cohen_d': 0.5, 'significant': True}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            
            save_results(results, output_path)
            
            df = pd.read_csv(output_path)
            
            assert len(df) == 1
            assert df.iloc[0]['alpha'] == 0.05
            assert df.iloc[0]['metric'] == 'episode_length'
            assert df.iloc[0]['p_value'] == 0.03
            assert df.iloc[0]['cohen_d'] == 0.5
            assert df.iloc[0]['significant'] == True


class TestCheckPrerequisites:
    """Tests for prerequisite checking."""

    def test_check_prerequisites_missing_file(self):
        """Should return False if results file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            assert not check_prerequisites(data_dir)

    def test_check_prerequisites_file_exists(self):
        """Should return True if results file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            results_file = data_dir / "simulation_results.json"
            
            with open(results_file, 'w') as f:
                json.dump([{'protocol': 'foundation', 'seed': 0}], f)
            
            assert check_prerequisites(data_dir)


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline(self):
        """Test the full pipeline from data generation to CSV output."""
        # Generate mock data
        mock_data = []
        for seed in range(30):
            mock_data.append({
                'protocol': 'foundation',
                'seed': seed,
                'episode_length': 80 + np.random.normal(0, 5),
                'messages': 40 + np.random.normal(0, 3),
                'bandwidth': 1000 + np.random.normal(0, 100),
                'latency': 50 + np.random.normal(0, 5)
            })
            mock_data.append({
                'protocol': 'native_direct',
                'seed': seed,
                'episode_length': 90 + np.random.normal(0, 5),
                'messages': 50 + np.random.normal(0, 3),
                'bandwidth': 1200 + np.random.normal(0, 100),
                'latency': 60 + np.random.normal(0, 5)
            })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            output_dir = Path(tmpdir) / "results"
            output_dir.mkdir()
            
            results_file = data_dir / "simulation_results.json"
            output_file = output_dir / "sensitivity_continuous.csv"
            
            # Save mock data
            with open(results_file, 'w') as f:
                json.dump(mock_data, f)
            
            # Run sensitivity sweep
            results = run_sensitivity_sweep(data_dir)
            
            # Save results
            save_results(results, output_file)
            
            # Verify output
            assert output_file.exists()
            df = pd.read_csv(output_file)
            
            # Verify schema
            expected_cols = ['alpha', 'metric', 'p_value', 'cohen_d', 'significant']
            assert list(df.columns) == expected_cols
            
            # Verify we have results for all metrics and alphas
            assert len(df) == len(CONTINUOUS_METRICS) * len(ALPHA_LEVELS)
            
            # Verify data types
            assert df['alpha'].dtype in ['float64', 'float32']
            assert df['p_value'].dtype in ['float64', 'float32']
            assert df['cohen_d'].dtype in ['float64', 'float32']
            assert df['significant'].dtype == 'bool'