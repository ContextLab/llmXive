"""
Tests for Pydantic schema validation in code/analysis/schemas.py.

These tests verify that:
1. SimulationSummaryRow validates correctly
2. StatisticalTestResults validates correctly
3. Invalid data raises appropriate errors
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pydantic import ValidationError
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.schemas import (
    SimulationSummaryRow,
    StatisticalTestResults,
    validate_simulation_summary_csv,
    validate_statistical_test_results,
    load_and_validate_simulation_summary,
    load_and_validate_statistical_test
)


class TestSimulationSummaryRow:
    """Tests for SimulationSummaryRow Pydantic model."""
    
    def test_valid_row(self):
        """Test that a valid row passes validation."""
        row = {
            'beta': 0.5,
            'method': 'mice',
            'estimator': 'ipw',
            'ate': 0.45,
            'bias': 0.05,
            'rmse': 0.07,
            'coverage_rate': 0.95,
            'seed': 42,
            'run_id': 'abc123',
            'ground_truth_ate': 0.5,
            'status': 'success',
            'vif': 2.5,
            'mnar_correlation': 0.3,
            'mnar_p_value': 0.01
        }
        model = SimulationSummaryRow(**row)
        assert model.beta == 0.5
        assert model.ate == 0.45
    
    def test_invalid_beta_range(self):
        """Test that beta outside [0, 1] raises error."""
        with pytest.raises(ValidationError):
            SimulationSummaryRow(
                beta=1.5,
                method='mice',
                estimator='ipw',
                ate=0.45,
                bias=0.05,
                rmse=0.07,
                coverage_rate=0.95,
                seed=42,
                run_id='abc123',
                ground_truth_ate=0.5
            )
    
    def test_infinite_ate_raises_error(self):
        """Test that infinite ATE raises error."""
        with pytest.raises(ValidationError):
            SimulationSummaryRow(
                beta=0.5,
                method='mice',
                estimator='ipw',
                ate=np.inf,
                bias=0.05,
                rmse=0.07,
                coverage_rate=0.95,
                seed=42,
                run_id='abc123',
                ground_truth_ate=0.5
            )
    
    def test_nan_ate_raises_error(self):
        """Test that NaN ATE raises error."""
        with pytest.raises(ValidationError):
            SimulationSummaryRow(
                beta=0.5,
                method='mice',
                estimator='ipw',
                ate=np.nan,
                bias=0.05,
                rmse=0.07,
                coverage_rate=0.95,
                seed=42,
                run_id='abc123',
                ground_truth_ate=0.5
            )
    
    def test_coverage_rate_bounds(self):
        """Test that coverage_rate must be in [0, 1]."""
        with pytest.raises(ValidationError):
            SimulationSummaryRow(
                beta=0.5,
                method='mice',
                estimator='ipw',
                ate=0.45,
                bias=0.05,
                rmse=0.07,
                coverage_rate=1.5,
                seed=42,
                run_id='abc123',
                ground_truth_ate=0.5
            )


class TestStatisticalTestResults:
    """Tests for StatisticalTestResults Pydantic model."""
    
    def test_valid_anova_result(self):
        """Test that a valid ANOVA result passes validation."""
        result = {
            'test_type': 'anova',
            'p_value': 0.03,
            'test_statistic': 4.5,
            'skewness': 0.5,
            'bootstrap_ci_diff': None
        }
        model = StatisticalTestResults(**result)
        assert model.test_type == 'anova'
    
    def test_valid_bootstrap_result(self):
        """Test that a valid bootstrap result passes validation."""
        result = {
            'test_type': 'bootstrap',
            'p_value': 0.02,
            'test_statistic': 3.8,
            'skewness': 1.5,
            'bootstrap_ci_diff': 0.12
        }
        model = StatisticalTestResults(**result)
        assert model.test_type == 'bootstrap'
        assert model.bootstrap_ci_diff == 0.12
    
    def test_skewness_requires_bootstrap_ci(self):
        """Test that |skewness| > 1 requires bootstrap_ci_diff."""
        with pytest.raises(ValidationError):
            StatisticalTestResults(
                test_type='bootstrap',
                p_value=0.02,
                test_statistic=3.8,
                skewness=1.5,
                bootstrap_ci_diff=None
            )
    
    def test_negative_skewness_requires_bootstrap_ci(self):
        """Test that negative skewness > 1 requires bootstrap_ci_diff."""
        with pytest.raises(ValidationError):
            StatisticalTestResults(
                test_type='bootstrap',
                p_value=0.02,
                test_statistic=3.8,
                skewness=-1.5,
                bootstrap_ci_diff=None
            )
    
    def test_invalid_p_value_range(self):
        """Test that p_value outside [0, 1] raises error."""
        with pytest.raises(ValidationError):
            StatisticalTestResults(
                test_type='anova',
                p_value=1.5,
                test_statistic=4.5,
                skewness=0.5,
                bootstrap_ci_diff=None
            )


class TestValidateSimulationSummaryCSV:
    """Tests for validate_simulation_summary_csv function."""
    
    def test_valid_dataframe(self):
        """Test that a valid DataFrame passes validation."""
        df = pd.DataFrame({
            'beta': [0.5],
            'method': ['mice'],
            'estimator': ['ipw'],
            'ate': [0.45],
            'bias': [0.05],
            'rmse': [0.07],
            'coverage_rate': [0.95],
            'seed': [42],
            'run_id': ['abc123'],
            'ground_truth_ate': [0.5],
            'status': ['success'],
            'vif': [2.5],
            'mnar_correlation': [0.3],
            'mnar_p_value': [0.01]
        })
        validate_simulation_summary_csv(df)
    
    def test_missing_column_raises_error(self):
        """Test that missing column raises error."""
        df = pd.DataFrame({
            'beta': [0.5],
            'method': ['mice'],
            # Missing other required columns
        })
        with pytest.raises(ValueError):
            validate_simulation_summary_csv(df)
    
    def test_extra_column_raises_error(self):
        """Test that extra column raises error."""
        df = pd.DataFrame({
            'beta': [0.5],
            'method': ['mice'],
            'estimator': ['ipw'],
            'ate': [0.45],
            'bias': [0.05],
            'rmse': [0.07],
            'coverage_rate': [0.95],
            'seed': [42],
            'run_id': ['abc123'],
            'ground_truth_ate': [0.5],
            'status': ['success'],
            'vif': [2.5],
            'mnar_correlation': [0.3],
            'mnar_p_value': [0.01],
            'extra_column': [1.0]  # Extra column
        })
        with pytest.raises(ValueError):
            validate_simulation_summary_csv(df)


class TestValidateStatisticalTestResults:
    """Tests for validate_statistical_test_results function."""
    
    def test_valid_json_file(self):
        """Test that a valid JSON file passes validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'test_type': 'anova',
                'p_value': 0.03,
                'test_statistic': 4.5,
                'skewness': 0.5,
                'bootstrap_ci_diff': None
            }, f)
            temp_path = f.name
        
        try:
            validate_statistical_test_results(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_invalid_json_file(self):
        """Test that invalid JSON file raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'test_type': 'anova',
                'p_value': 1.5,  # Invalid p-value
                'test_statistic': 4.5,
                'skewness': 0.5,
                'bootstrap_ci_diff': None
            }, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                validate_statistical_test_results(temp_path)
        finally:
            os.unlink(temp_path)