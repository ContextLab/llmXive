"""
Unit tests for the profiler module.
"""
import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.diagnostic import het_breuschpagan
import statsmodels.api as sm

from src.ingestion.profiler import (
    classify_bp_severity,
    classify_cooks_severity,
    classify_condition_number_severity,
    compute_condition_number,
    compute_breusch_pagan,
    compute_cooks_distance,
    classify_violation_severity,
    profile_dataset
)
from src.models.data_models import DatasetProfile


class TestClassifyBPSeverity:
    def test_high_severity_low_pvalue(self):
        """Test that low p-value returns High severity"""
        result = classify_bp_severity(10.0, 0.01)
        assert result == "High"

    def test_medium_severity_medium_pvalue(self):
        """Test that medium p-value returns Medium severity"""
        result = classify_bp_severity(10.0, 0.07)
        assert result == "Medium"

    def test_low_severity_high_pvalue(self):
        """Test that high p-value returns Low severity"""
        result = classify_bp_severity(10.0, 0.2)
        assert result == "Low"

    def test_unknown_severity_nan_pvalue(self):
        """Test that NaN p-value returns Unknown severity"""
        result = classify_bp_severity(10.0, np.nan)
        assert result == "Unknown"

    def test_unknown_severity_none_pvalue(self):
        """Test that None p-value returns Unknown severity"""
        result = classify_bp_severity(10.0, None)
        assert result == "Unknown"


class TestClassifyCooksSeverity:
    def test_high_severity_large_cooks(self):
        """Test that Cook's distance > 1 returns High severity"""
        result = classify_cooks_severity(1.5, 100)
        assert result == "High"

    def test_medium_severity_threshold_4n(self):
        """Test that Cook's distance > 4/n returns Medium severity"""
        n = 100
        threshold = 4.0 / n
        result = classify_cooks_severity(threshold * 2, n)
        assert result == "Medium"

    def test_low_severity_small_cooks(self):
        """Test that small Cook's distance returns Low severity"""
        result = classify_cooks_severity(0.01, 100)
        assert result == "Low"


class TestClassifyConditionNumberSeverity:
    def test_high_severity_very_large_cond(self):
        """Test that very large condition number returns High severity"""
        result = classify_condition_number_severity(1500.0)
        assert result == "High"

    def test_medium_severity_large_cond(self):
        """Test that large condition number returns Medium severity"""
        result = classify_condition_number_severity(150.0)
        assert result == "Medium"

    def test_high_severity_above_30(self):
        """Test that condition number > 30 returns High (multicollinearity concern)"""
        result = classify_condition_number_severity(50.0)
        assert result == "High"

    def test_low_severity_small_cond(self):
        """Test that small condition number returns Low severity"""
        result = classify_condition_number_severity(10.0)
        assert result == "Low"

    def test_critical_severity_inf(self):
        """Test that infinite condition number returns Critical"""
        result = classify_condition_number_severity(float('inf'))
        assert result == "Critical"

    def test_critical_severity_nan(self):
        """Test that NaN condition number returns Critical"""
        result = classify_condition_number_severity(float('nan'))
        assert result == "Critical"


class TestComputeConditionNumber:
    def test_well_conditioned_matrix(self):
        """Test condition number computation on well-conditioned matrix"""
        X = np.eye(10)
        cond = compute_condition_number(X)
        assert cond == pytest.approx(1.0, rel=1e-5)

    def test_multicollinear_matrix(self):
        """Test condition number computation on multicollinear matrix"""
        X = np.column_stack([np.ones(100), np.random.randn(100), np.random.randn(100) * 1000])
        cond = compute_condition_number(X)
        assert cond > 30  # Should detect multicollinearity

    def test_single_column(self):
        """Test condition number on single column matrix"""
        X = np.random.randn(100, 1)
        cond = compute_condition_number(X)
        assert cond > 0

    def test_empty_matrix(self):
        """Test condition number on empty matrix"""
        X = np.array([]).reshape(10, 0)
        cond = compute_condition_number(X)
        assert cond == 0.0


class TestComputeBreuschPagan:
    def test_heteroskedastic_data(self):
        """Test BP test on heteroskedastic data"""
        np.random.seed(42)
        n = 200
        X = np.random.randn(n, 2)
        # Create heteroskedastic errors
        errors = np.random.randn(n) * (1 + X[:, 0]**2)
        y = X @ [1, 2] + errors

        stat, pval = compute_breusch_pagan(y, X)
        assert not np.isnan(stat)
        assert not np.isnan(pval)
        assert stat >= 0
        assert 0 <= pval <= 1

    def test_homoskedastic_data(self):
        """Test BP test on homoskedastic data"""
        np.random.seed(42)
        n = 200
        X = np.random.randn(n, 2)
        errors = np.random.randn(n)  # Homoskedastic
        y = X @ [1, 2] + errors

        stat, pval = compute_breusch_pagan(y, X)
        assert not np.isnan(stat)
        assert not np.isnan(pval)


class TestComputeCooksDistance:
    def test_no_influential_points(self):
        """Test Cook's distance on data without influential points"""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 2)
        y = X @ [1, 2] + np.random.randn(n) * 0.1

        max_cooks = compute_cooks_distance(y, X)
        assert not np.isnan(max_cooks)
        assert max_cooks >= 0

    def test_with_influential_point(self):
        """Test Cook's distance detects influential points"""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 2)
        y = X @ [1, 2] + np.random.randn(n) * 0.1

        # Add an influential point
        X = np.vstack([X, [10, 10]])
        y = np.append(y, 100)

        max_cooks = compute_cooks_distance(y, X)
        assert not np.isnan(max_cooks)
        assert max_cooks > 0


class TestClassifyViolationSeverity:
    def test_all_low_severity(self):
        """Test classification when all metrics show low severity"""
        result = classify_violation_severity(
            bp_stat=5.0,
            bp_pvalue=0.5,
            max_cooks=0.01,
            condition_number=15.0,
            n_observations=100
        )
        assert result["breusch_pagan"] == "Low"
        assert result["cooks_distance"] == "Low"
        assert result["condition_number"] == "Low"
        assert result["multicollinearity_detected"] is False

    def test_high_multicollinearity(self):
        """Test classification when multicollinearity is high"""
        result = classify_violation_severity(
            bp_stat=5.0,
            bp_pvalue=0.5,
            max_cooks=0.01,
            condition_number=150.0,
            n_observations=100
        )
        assert result["condition_number"] == "Medium"
        assert result["multicollinearity_detected"] is True

    def test_high_bp_severity(self):
        """Test classification when BP shows high severity"""
        result = classify_violation_severity(
            bp_stat=20.0,
            bp_pvalue=0.01,
            max_cooks=0.01,
            condition_number=15.0,
            n_observations=100
        )
        assert result["breusch_pagan"] == "High"


class TestProfileDataset:
    def test_profile_small_dataset(self):
        """Test profiling a small dataset"""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'target': np.random.randn(n),
            'feat1': np.random.randn(n),
            'feat2': np.random.randn(n)
        })

        profile = profile_dataset(df, 'target', ['feat1', 'feat2'])

        assert isinstance(profile, DatasetProfile)
        assert profile.n_observations == n
        assert profile.n_features == 2
        assert not np.isnan(profile.condition_number)
        assert not np.isnan(profile.breusch_pagan_stat)
        assert not np.isnan(profile.max_cooks_distance)
        assert profile.violation_severity is not None

    def test_profile_with_subsample(self):
        """Test profiling with subsampling"""
        np.random.seed(42)
        n = 500
        df = pd.DataFrame({
            'target': np.random.randn(n),
            'feat1': np.random.randn(n),
            'feat2': np.random.randn(n)
        })

        profile = profile_dataset(df, 'target', ['feat1', 'feat2'], subsample_size=100)

        assert profile.n_observations == 100
        assert profile.n_features == 2

    def test_profile_multicollinearity_detection(self):
        """Test that multicollinearity is correctly detected"""
        np.random.seed(42)
        n = 100
        # Create highly correlated features
        feat1 = np.random.randn(n)
        feat2 = feat1 * 100 + np.random.randn(n) * 0.1

        df = pd.DataFrame({
            'target': np.random.randn(n),
            'feat1': feat1,
            'feat2': feat2
        })

        profile = profile_dataset(df, 'target', ['feat1', 'feat2'])

        # Condition number should be high
        assert profile.condition_number > 30
        assert profile.multicollinearity_detected is True
        assert profile.violation_severity["condition_number"] != "Low"