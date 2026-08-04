"""
Tests for T029c: Data Aggregation module.
"""
import os
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.aggregation import (
    compute_run_id,
    calculate_coverage_rate,
    aggregate_results,
    save_summary_dataframe,
    RESULTS_DIR,
    SUMMARY_OUTPUT
)
from analysis.entities import CausalEstimate

class TestComputeRunId:
    def test_compute_run_id_deterministic(self):
        """Test that run ID is deterministic for same seed and beta."""
        run_id_1 = compute_run_id(42, 0.5)
        run_id_2 = compute_run_id(42, 0.5)
        assert run_id_1 == run_id_2
        assert len(run_id_1) == 64  # SHA-256 hex length
    
    def test_compute_run_id_unique(self):
        """Test that different seeds/betas produce different run IDs."""
        run_id_1 = compute_run_id(42, 0.5)
        run_id_2 = compute_run_id(43, 0.5)
        run_id_3 = compute_run_id(42, 0.8)
        assert run_id_1 != run_id_2
        assert run_id_1 != run_id_3

class TestCalculateCoverageRate:
    def test_coverage_rate_all_contain(self):
        """Test coverage rate when all CIs contain ground truth."""
        estimates = [
            CausalEstimate(ate=0.5, se=0.1, lower_ci=0.3, upper_ci=0.7, method="mean", estimator="ipw", seed=1),
            CausalEstimate(ate=0.5, se=0.1, lower_ci=0.4, upper_ci=0.6, method="mean", estimator="ipw", seed=2),
            CausalEstimate(ate=0.5, se=0.1, lower_ci=0.35, upper_ci=0.65, method="mean", estimator="ipw", seed=3),
        ]
        coverage = calculate_coverage_rate(estimates, 0.5)
        assert coverage == 1.0
    
    def test_coverage_rate_none_contain(self):
        """Test coverage rate when no CIs contain ground truth."""
        estimates = [
            CausalEstimate(ate=1.0, se=0.1, lower_ci=0.8, upper_ci=1.2, method="mean", estimator="ipw", seed=1),
            CausalEstimate(ate=1.0, se=0.1, lower_ci=0.9, upper_ci=1.1, method="mean", estimator="ipw", seed=2),
        ]
        coverage = calculate_coverage_rate(estimates, 0.5)
        assert coverage == 0.0
    
    def test_coverage_rate_partial(self):
        """Test coverage rate when some CIs contain ground truth."""
        estimates = [
            CausalEstimate(ate=0.5, se=0.1, lower_ci=0.3, upper_ci=0.7, method="mean", estimator="ipw", seed=1),
            CausalEstimate(ate=1.0, se=0.1, lower_ci=0.8, upper_ci=1.2, method="mean", estimator="ipw", seed=2),
            CausalEstimate(ate=0.5, se=0.1, lower_ci=0.4, upper_ci=0.6, method="mean", estimator="ipw", seed=3),
        ]
        coverage = calculate_coverage_rate(estimates, 0.5)
        assert coverage == 2/3
    
    def test_coverage_rate_empty(self):
        """Test coverage rate with empty list."""
        coverage = calculate_coverage_rate([], 0.5)
        assert coverage == 0.0

class TestAggregationIntegration:
    @pytest.fixture
    def temp_results_dir(self):
        """Create a temporary directory with mock run results."""
        temp_dir = tempfile.mkdtemp()
        results_dir = os.path.join(temp_dir, "data", "results")
        os.makedirs(results_dir)
        
        # Create mock run results
        mock_run_1 = {
            "seed": 42,
            "beta": 0.5,
            "ground_truth_ate": 0.5,
            "alpha": 0.3,
            "status": "completed",
            "results": {
                "mean": {
                    "ipw": {
                        "ate": 0.52,
                        "se": 0.05,
                        "lower_ci": 0.42,
                        "upper_ci": 0.62
                    },
                    "psm": {
                        "ate": 0.51,
                        "se": 0.06,
                        "lower_ci": 0.39,
                        "upper_ci": 0.63
                    }
                },
                "knn": {
                    "ipw": {
                        "ate": 0.53,
                        "se": 0.04,
                        "lower_ci": 0.45,
                        "upper_ci": 0.61
                    }
                }
            }
        }
        
        mock_run_2 = {
            "seed": 43,
            "beta": 0.8,
            "ground_truth_ate": 0.5,
            "alpha": 0.5,
            "status": "completed",
            "results": {
                "mean": {
                    "ipw": {
                        "ate": 0.55,
                        "se": 0.07,
                        "lower_ci": 0.41,
                        "upper_ci": 0.69
                    }
                }
            }
        }
        
        with open(os.path.join(results_dir, "run_42_0.5.json"), 'w') as f:
            json.dump(mock_run_1, f)
        
        with open(os.path.join(results_dir, "run_43_0.8.json"), 'w') as f:
            json.dump(mock_run_2, f)
        
        yield results_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_aggregate_results_schema(self, temp_results_dir):
        """Test that aggregate results have correct schema."""
        with patch('code.analysis.aggregation.RESULTS_DIR', temp_results_dir):
            df = aggregate_results()
            
            expected_columns = [
                'beta', 'method', 'estimator', 'ate', 'bias', 'rmse', 
                'coverage_rate', 'seed', 'run_id', 'ground_truth_ate', 
                'beta_value', 'status'
            ]
            
            for col in expected_columns:
                assert col in df.columns, f"Missing column: {col}"
    
    def test_aggregate_results_values(self, temp_results_dir):
        """Test that aggregated values are calculated correctly."""
        with patch('code.analysis.aggregation.RESULTS_DIR', temp_results_dir):
            df = aggregate_results()
            
            # Check specific values
            # Run 1 (seed=42, beta=0.5, gt=0.5): mean+ipw ate=0.52 -> bias=0.02
            row = df[(df['seed'] == 42) & (df['method'] == 'mean') & (df['estimator'] == 'ipw')]
            assert len(row) == 1
            assert abs(row['bias'].values[0] - 0.02) < 1e-6
            assert row['coverage_rate'].values[0] == 1.0  # 0.42 <= 0.5 <= 0.62
            
            # Run 2 (seed=43, beta=0.8, gt=0.5): mean+ipw ate=0.55 -> bias=0.05
            row = df[(df['seed'] == 43) & (df['method'] == 'mean') & (df['estimator'] == 'ipw')]
            assert len(row) == 1
            assert abs(row['bias'].values[0] - 0.05) < 1e-6
    
    def test_save_summary_dataframe(self, temp_results_dir):
        """Test saving summary to CSV."""
        with patch('code.analysis.aggregation.RESULTS_DIR', temp_results_dir):
            df = aggregate_results()
            
            output_path = os.path.join(temp_results_dir, "test_summary.csv")
            with patch('code.analysis.aggregation.SUMMARY_OUTPUT', output_path):
                saved_path = save_summary_dataframe(df, output_path)
            
            assert os.path.exists(saved_path)
            
            # Verify CSV can be read back
            df_read = pd.read_csv(saved_path)
            assert len(df_read) == len(df)
            assert list(df_read.columns) == list(df.columns)