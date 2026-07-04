import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Also handle 'code' directory structure
code_dir = current_dir.parent.parent.parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from src.evaluation.metrics import (
    calculate_rmse, 
    calculate_mae, 
    evaluate_frequentist_forecasts,
    calculate_coverage,
    test_coverage_reliability
)

class TestCalculateRMSE:
    def test_basic_rmse(self):
        """Test basic RMSE calculation"""
        predictions = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        actuals = pd.Series([1.1, 2.1, 2.9, 4.2, 4.8])
        
        rmse = calculate_rmse(predictions, actuals)
        expected_rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
        
        assert np.isclose(rmse, expected_rmse)
        
    def test_perfect_prediction(self):
        """Test RMSE when predictions match actuals"""
        predictions = pd.Series([1.0, 2.0, 3.0])
        actuals = pd.Series([1.0, 2.0, 3.0])
        
        rmse = calculate_rmse(predictions, actuals)
        assert rmse == 0.0
        
    def test_empty_series(self):
        """Test RMSE with empty series"""
        predictions = pd.Series([], dtype=float)
        actuals = pd.Series([], dtype=float)
        
        rmse = calculate_rmse(predictions, actuals)
        assert rmse == 0.0
        
    def test_mismatched_lengths(self):
        """Test RMSE with mismatched lengths raises error"""
        predictions = pd.Series([1.0, 2.0, 3.0])
        actuals = pd.Series([1.0, 2.0])
        
        with pytest.raises(ValueError):
            calculate_rmse(predictions, actuals)

class TestCalculateMAE:
    def test_basic_mae(self):
        """Test basic MAE calculation"""
        predictions = pd.Series([1.0, 2.0, 3.0, 4.0])
        actuals = pd.Series([1.5, 2.5, 2.5, 4.5])
        
        mae = calculate_mae(predictions, actuals)
        expected_mae = np.mean(np.abs(predictions - actuals))
        
        assert np.isclose(mae, expected_mae)
        
    def test_perfect_prediction(self):
        """Test MAE when predictions match actuals"""
        predictions = pd.Series([1.0, 2.0, 3.0])
        actuals = pd.Series([1.0, 2.0, 3.0])
        
        mae = calculate_mae(predictions, actuals)
        assert mae == 0.0
        
    def test_empty_series(self):
        """Test MAE with empty series"""
        predictions = pd.Series([], dtype=float)
        actuals = pd.Series([], dtype=float)
        
        mae = calculate_mae(predictions, actuals)
        assert mae == 0.0

class TestEvaluateFrequentistForecasts:
    def test_evaluate_with_data(self):
        """Test evaluation with sample forecast data"""
        forecasts = pd.DataFrame({
            'simple_avg_forecast': [45.0, 48.0, 52.0, 55.0],
            'weighted_avg_forecast': [45.5, 47.5, 52.5, 54.5],
            'actual_outcome': [46.0, 47.0, 53.0, 54.0]
        })
        
        outcomes = pd.DataFrame()  # Not used in this implementation
        
        results = evaluate_frequentist_forecasts(forecasts, outcomes)
        
        assert 'method' in results.columns
        assert 'rmse' in results.columns
        assert 'mae' in results.columns
        assert len(results) == 2  # Two methods
        
    def test_missing_columns(self):
        """Test evaluation with missing forecast columns"""
        forecasts = pd.DataFrame({
            'actual_outcome': [46.0, 47.0, 53.0, 54.0]
        })
        
        outcomes = pd.DataFrame()
        
        results = evaluate_frequentist_forecasts(forecasts, outcomes)
        assert len(results) == 0  # No valid methods to evaluate

class TestCalculateCoverage:
    def test_basic_coverage(self):
        """Test basic coverage calculation"""
        lower = pd.Series([40.0, 45.0, 50.0])
        upper = pd.Series([50.0, 55.0, 60.0])
        actuals = pd.Series([45.0, 50.0, 55.0])  # All within intervals
        
        coverage = calculate_coverage(lower, upper, actuals)
        assert coverage == 1.0
        
    def test_partial_coverage(self):
        """Test coverage with some values outside intervals"""
        lower = pd.Series([40.0, 45.0, 50.0])
        upper = pd.Series([50.0, 55.0, 60.0])
        actuals = pd.Series([45.0, 60.0, 55.0])  # One outside
        
        coverage = calculate_coverage(lower, upper, actuals)
        assert coverage == 2/3
        
    def test_no_coverage(self):
        """Test coverage with no values within intervals"""
        lower = pd.Series([40.0, 45.0, 50.0])
        upper = pd.Series([50.0, 55.0, 60.0])
        actuals = pd.Series([30.0, 70.0, 80.0])  # All outside
        
        coverage = calculate_coverage(lower, upper, actuals)
        assert coverage == 0.0
        
    def test_empty_series(self):
        """Test coverage with empty series"""
        lower = pd.Series([], dtype=float)
        upper = pd.Series([], dtype=float)
        actuals = pd.Series([], dtype=float)
        
        coverage = calculate_coverage(lower, upper, actuals)
        assert coverage == 0.0

class TestCoverageReliability:
    def test_perfect_coverage(self):
        """Test binomial test with perfect coverage"""
        results = test_coverage_reliability(
            coverage_rate=0.95,
            n_observations=100,
            target_coverage=0.95,
            alpha=0.05
        )
        
        assert results['reject_null'] == False
        assert 'consistent' in results['conclusion'].lower()
        
    def test_under_coverage(self):
        """Test binomial test with significantly low coverage"""
        # With n=100, observed=0.85, target=0.95
        # This should likely reject the null
        results = test_coverage_reliability(
            coverage_rate=0.85,
            n_observations=100,
            target_coverage=0.95,
            alpha=0.05
        )
        
        # The conclusion should mention under-coverage
        assert 'lower' in results['conclusion'].lower() or 'under' in results['conclusion'].lower()
        
    def test_over_coverage(self):
        """Test binomial test with significantly high coverage"""
        results = test_coverage_reliability(
            coverage_rate=0.99,
            n_observations=100,
            target_coverage=0.95,
            alpha=0.05
        )
        
        # The conclusion should mention over-coverage or higher
        assert 'higher' in results['conclusion'].lower() or 'over' in results['conclusion'].lower()
        
    def test_zero_observations(self):
        """Test binomial test with no observations"""
        results = test_coverage_reliability(
            coverage_rate=0.0,
            n_observations=0,
            target_coverage=0.95,
            alpha=0.05
        )
        
        assert results['reject_null'] == False
        assert 'no observations' in results['conclusion'].lower()
        
    def test_statistical_properties(self):
        """Test that test returns expected statistical properties"""
        results = test_coverage_reliability(
            coverage_rate=0.90,
            n_observations=200,
            target_coverage=0.95,
            alpha=0.05
        )
        
        assert 'statistic' in results
        assert 'p_value' in results
        assert 'reject_null' in results
        assert 'conclusion' in results
        assert results['n_observations'] == 200
        assert results['target_coverage'] == 0.95
        assert results['alpha'] == 0.05