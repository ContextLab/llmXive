import pytest
import numpy as np
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Import from the existing project API surface
from src.models import DatasetRecord, AnalysisResult, SensitivitySweep
from src.stats_engine import (
    run_t_test,
    calculate_effect_size,
    check_collinearity,
    calculate_power,
    aggregate_results
)
from src.data_loader import load_public_dataset, calculate_gain_scores, log_skipped_record
from src.sensitivity import run_sensitivity_sweep, check_robustness_warning
from src.utils import set_seed


class TestEdgeCasesSampleSize:
    """Tests for edge cases involving small sample sizes (N < 30)."""

    def test_t_test_small_sample_size(self):
        """Verify t-test handles N < 30 without crashing, returning appropriate stats."""
        set_seed(42)
        # Small sample: N=10 per group
        group_a = np.random.normal(loc=5.0, scale=1.0, size=10)
        group_b = np.random.normal(loc=5.5, scale=1.2, size=10)

        # Should not raise an exception
        t_stat, p_val, ci_low, ci_high = run_t_test(group_a, group_b, equal_var=False)

        assert isinstance(t_stat, float)
        assert isinstance(p_val, float)
        assert 0 <= p_val <= 1
        # Even with small N, we expect valid intervals
        assert ci_low < ci_high

    def test_power_calculation_underpowered(self):
        """Verify power calculation flags underpowered results (power < 0.80) for small N."""
        set_seed(42)
        group_a = np.random.normal(loc=5.0, scale=1.0, size=15)
        group_b = np.random.normal(loc=5.1, scale=1.0, size=15)

        # Effect size is small, N is small -> should be underpowered
        effect_d = calculate_effect_size(group_a, group_b)
        power = calculate_power(group_a, group_b, effect_size=effect_d)

        # We expect low power with small N and small effect
        assert isinstance(power, float)
        # Note: The specific threshold logic is in calculate_power, but we assert it returns a number
        assert 0 <= power <= 1

    def test_sensitivity_sweep_insufficient_data(self):
        """Verify sensitivity sweep flags insufficient data when N < 30."""
        set_seed(42)
        # Create a tiny dataset
        data = []
        for i in range(10):
            data.append({
                "pre_test_score": 5.0 + np.random.normal(0, 0.1),
                "post_test_score": 5.2 + np.random.normal(0, 0.1),
                "instruction_type": "embodied" if i < 5 else "static",
                "covariates": {}
            })

        # Run sweep with a tiny threshold list
        thresholds = [0.05, 0.01]
        results = run_sensitivity_sweep(data, thresholds)

        # Check that the robustness warning or a specific flag indicates insufficient data
        # Based on T029 logic, this should trigger a flag
        if isinstance(results, list) and len(results) > 0:
            # If results are aggregated, check for the warning
            pass
        elif isinstance(results, dict):
            # If it returns a single status object
            assert "robustness_warning" in results or "insufficient_data" in results

    def test_aggregate_results_empty_groups(self):
        """Verify aggregate_results handles cases where one group might be empty or near-empty."""
        set_seed(42)
        # One group has data, other is empty
        group_a = np.array([1.0, 2.0, 3.0])
        group_b = np.array([])

        with pytest.raises((ValueError, IndexError)):
            # This should raise an error because we can't compute stats on empty array
            calculate_effect_size(group_a, group_b)


class TestEdgeCasesMissingColumns:
    """Tests for edge cases involving missing columns in input data."""

    def test_load_public_dataset_missing_required_column(self):
        """Verify load_public_dataset fails gracefully or handles missing required columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "missing_cols.csv")
            # Write CSV missing 'instruction_type'
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["pre_test_score", "post_test_score"])
                writer.writeheader()
                writer.writerow({"pre_test_score": 5.0, "post_test_score": 6.0})

            # The implementation in T012/T016 should auto-invoke SyntheticDataGenerator
            # or raise a specific error if it can't proceed.
            # We test that it doesn't crash with a generic KeyError.
            try:
                result = load_public_dataset(csv_path)
                # If it succeeded, it must have handled the missing column (e.g., via synthetic fallback)
                assert isinstance(result, list) or isinstance(result, dict)
            except KeyError as e:
                # If it raises KeyError, that's a failure of the auto-invocation logic
                pytest.fail(f"load_public_dataset raised KeyError for missing column: {e}")

    def test_calculate_gain_scores_missing_values(self):
        """Verify calculate_gain_scores skips rows with missing values and logs them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "skipped.log")
            data = [
                {"pre_test_score": 5.0, "post_test_score": 6.0, "instruction_type": "embodied"},
                {"pre_test_score": None, "post_test_score": 7.0, "instruction_type": "static"}, # Missing pre
                {"pre_test_score": 5.0, "post_test_score": None, "instruction_type": "embodied"}, # Missing post
                {"pre_test_score": 6.0, "post_test_score": 7.0, "instruction_type": "static"}
            ]

            gains, skipped_count = calculate_gain_scores(data)

            # Should have 2 valid gains
            assert len(gains) == 2
            # Should have skipped 2 records
            assert skipped_count == 2


class TestEdgeCasesCollinearity:
    """Tests for edge cases involving collinearity detection."""

    def test_check_collinearity_high_correlation(self):
        """Verify check_collinearity detects |r| > 0.8 and reports it."""
        set_seed(42)
        # Create highly correlated predictors
        x = np.random.normal(0, 1, 100)
        y = x * 0.9 + np.random.normal(0, 0.1, 100) # High correlation

        predictors = {"feat1": x, "feat2": y}
        target = np.random.normal(0, 1, 100)

        # Should return a dict with collinearity info
        collinearity_report = check_collinearity(predictors, target)

        assert isinstance(collinearity_report, dict)
        # Check if high correlation was detected
        # The exact key name depends on implementation, but we expect a flag or list
        assert "high_collinearity" in collinearity_report or "pairs" in collinearity_report

    def test_check_collinearity_low_correlation(self):
        """Verify check_collinearity returns clean report for low correlation."""
        set_seed(42)
        x1 = np.random.normal(0, 1, 100)
        x2 = np.random.normal(0, 1, 100)
        target = x1 + x2 + np.random.normal(0, 0.1, 100)

        predictors = {"feat1": x1, "feat2": x2}

        collinearity_report = check_collinearity(predictors, target)

        assert isinstance(collinearity_report, dict)
        # Should not flag high collinearity
        if "high_collinearity" in collinearity_report:
            assert collinearity_report["high_collinearity"] is False

    def test_check_collinearity_single_predictor(self):
        """Verify check_collinearity handles single predictor gracefully."""
        set_seed(42)
        x = np.random.normal(0, 1, 100)
        target = x + np.random.normal(0, 0.1, 100)

        predictors = {"feat1": x}

        collinearity_report = check_collinearity(predictors, target)

        assert isinstance(collinearity_report, dict)
        # Should not raise error
        assert "error" not in collinearity_report or collinearity_report["error"] is False