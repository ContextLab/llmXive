"""
Unit tests for estimators (T003).

Verifies:
- tau^2 = 0 stability (DL and REML converge to the FE result).
- Pooled estimates match known normal cases within 0.001.
- Q and I^2 statistics are computed for every estimation.
- Small-study (N < 5) datasets are explicitly flagged.
- REML convergence failures are logged to data/results/reml_failures.json
  and the estimator proceeds with a fallback variance (FR-006).
"""

import json
import math
import os
from pathlib import Path

import pytest

from code.simulation.estimators import (
    estimate_fixed_effects,
    estimate_dersimonian_laird,
    estimate_reml,
    apply_estimator,
    calculate_i_squared,
    log_reml_failure,
    REML_FAILURE_LOG_PATH,
)


class TestFixedEffects:
    def test_known_case_equal_variances(self):
        """Two studies, equal SEs: pooled must equal the simple mean."""
        effects = [1.0, 2.0]
        variances = [1.0, 1.0]
        result = estimate_fixed_effects(effects, variances)
        assert math.isclose(result.pooled_effect, 1.5, abs_tol=0.001)
        assert result.tau2 == 0.0
        assert result.convergence_status == "success"

    def test_identical_effects_zero_heterogeneity(self):
        """Identical effect sizes: Q = 0, I^2 = 0, pooled = effect."""
        effects = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        variances = [0.04] * 6
        result = estimate_fixed_effects(effects, variances)
        assert math.isclose(result.pooled_effect, 0.5, abs_tol=0.001)
        assert result.q_statistic == pytest.approx(0.0, abs=1e-12)
        assert result.i2 == 0.0
        assert result.tau2 == 0.0

    def test_weighted_known_case(self):
        """Known inverse-variance weighted mean."""
        effects = [0.2, 0.4]
        variances = [0.01, 0.04]  # weights 100 and 25
        result = estimate_fixed_effects(effects, variances)
        expected = (100 * 0.2 + 25 * 0.4) / 125
        assert math.isclose(result.pooled_effect, expected, abs_tol=0.001)
        # SE = sqrt(1/125)
        assert math.isclose(result.se_pooled, math.sqrt(1.0 / 125.0), abs_tol=0.001)

    def test_ci_symmetry(self):
        effects = [0.3, 0.7, 0.5, 0.4, 0.6, 0.5]
        variances = [0.02] * 6
        result = estimate_fixed_effects(effects, variances)
        assert result.ci_lower < result.pooled_effect < result.ci_upper
        assert math.isclose(
            result.ci_upper - result.pooled_effect,
            result.pooled_effect - result.ci_lower,
            abs_tol=1e-12
        )

    def test_input_validation(self):
        with pytest.raises(ValueError):
            estimate_fixed_effects([1.0], [])
        with pytest.raises(ValueError):
            estimate_fixed_effects([], [])
        with pytest.raises(ValueError):
            estimate_fixed_effects([1.0, 2.0], [0.1])  # length mismatch
        with pytest.raises(ValueError):
            estimate_fixed_effects([1.0, 2.0], [0.0, 0.1])  # non-positive variance


class TestDerSimonianLaird:
    def test_tau2_zero_stability(self):
        """With homogenous effects, DL tau^2 must be exactly 0 and the
        pooled estimate must match the FE estimate."""
        effects = [0.5] * 6
        variances = [0.01] * 6
        fe = estimate_fixed_effects(effects, variances)
        dl = estimate_dersimonian_laird(effects, variances)
        assert dl.tau2 == 0.0
        assert math.isclose(dl.pooled_effect, fe.pooled_effect, abs_tol=0.001)
        assert math.isclose(dl.se_pooled, fe.se_pooled, abs_tol=0.001)

    def test_known_heterogeneous_case(self):
        """Known DL calculation: equal variances => DL tau^2 equals the
        sample variance of the effects (with ddof=1)."""
        effects = [1.0, 2.0, 3.0]
        variances = [1.0, 1.0, 1.0]
        result = estimate_dersimonian_laird(effects, variances)
        # Q = sum((y - 2)^2) = 2, df = 2, C = 3 - 3/3 = 2
        # tau^2 = max(0, (2 - 2) / 2) = 0
        assert result.tau2 == pytest.approx(0.0, abs=1e-12)
        assert math.isclose(result.pooled_effect, 2.0, abs_tol=0.001)

    def test_positive_tau2(self):
        """Strong between-study spread with small within-study variance."""
        effects = [0.0, 1.0, 2.0, 3.0, 4.0]
        variances = [0.01] * 5
        result = estimate_dersimonian_laird(effects, variances)
        assert result.tau2 > 0.0
        assert result.i2 > 0.0

    def test_single_study_falls_back_to_fe(self):
        result = estimate_dersimonian_laird([1.0], [1.0])
        assert result.pooled_effect == 1.0
        assert result.tau2 == 0.0


class TestREML:
    def test_basic_convergence(self):
        effects = [0.5, 0.6, 0.4, 0.7, 0.5]
        variances = [0.04] * 5
        result = estimate_reml(effects, variances)
        assert result.convergence_status == "success"
        assert result.pooled_effect is not None
        assert result.ci_lower < result.ci_upper

    def test_tau2_zero_stability(self):
        """Homogeneous effects: REML tau^2 must be ~0 and the pooled
        estimate must match FE within 0.001."""
        effects = [0.5] * 6
        variances = [0.01] * 6
        fe = estimate_fixed_effects(effects, variances)
        reml = estimate_reml(effects, variances)
        assert reml.tau2 == pytest.approx(0.0, abs=1e-4)
        assert math.isclose(reml.pooled_effect, fe.pooled_effect, abs_tol=0.001)

    def test_homogeneous_normal_case_matches_mean(self):
        """Known normal case: equal-variance studies => pooled = mean."""
        effects = [0.2, 0.4, 0.6, 0.8, 1.0]
        variances = [0.05] * 5
        result = estimate_reml(effects, variances)
        assert math.isclose(result.pooled_effect, 0.6, abs_tol=0.001)

    def test_single_study_falls_back_to_fe(self):
        result = estimate_reml([1.0], [1.0])
        assert result.pooled_effect == 1.0
        assert result.convergence_status == "success"

    def test_failure_logging_and_fallback(self, tmp_path, monkeypatch):
        """FR-006: a REML failure must be logged to the JSON log and the
        estimator must proceed with a fallback (DL) variance."""
        log_file = tmp_path / "reml_failures.json"
        monkeypatch.setattr(
            "code.simulation.estimators.REML_FAILURE_LOG_PATH", str(log_file)
        )
        # Force the optimizer to fail by making the objective raise.
        import code.simulation.estimators as est_mod

        def broken_objective(tau2):
            raise RuntimeError("simulated optimizer crash")

        real_minimize_scalar = est_mod.optimize.minimize_scalar
        monkeypatch.setattr(
            est_mod.optimize, "minimize_scalar",
            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("simulated crash"))
        )
        try:
            effects = [0.5, 0.6, 0.4, 0.7, 0.5]
            variances = [0.04] * 5
            result = est_mod.estimate_reml(effects, variances)
            # Fallback result must still be a valid estimation
            assert result.convergence_status == "fallback_dl"
            assert result.pooled_effect is not None
            assert result.ci_lower < result.ci_upper
            # Failure must be logged
            assert log_file.exists()
            with open(log_file) as f:
                events = json.load(f)
            assert len(events) >= 1
            assert events[-1]["estimator"] == "reml"
            assert "fallback" in events[-1]
        finally:
            monkeypatch.setattr(
                est_mod.optimize, "minimize_scalar", real_minimize_scalar
            )


class TestHeterogeneityStatistics:
    def test_q_and_i2_always_computed(self):
        """Constitution Principle VII: Q and I^2 for every estimation."""
        effects = [0.1, 0.5, 0.9, 0.3, 0.7]
        variances = [0.02] * 5
        for est in (estimate_fixed_effects, estimate_dersimonian_laird, estimate_reml):
            result = est(effects, variances)
            assert result.q_statistic >= 0.0
            assert 0.0 <= result.i2 <= 100.0
            assert result.df == 4

    def test_i_squared_formula(self):
        assert calculate_i_squared(10.0, 4) == pytest.approx(60.0)
        assert calculate_i_squared(4.0, 4) == pytest.approx(0.0)
        assert calculate_i_squared(2.0, 4) == 0.0  # Q < df clamps to 0
        assert calculate_i_squared(0.0, 4) == 0.0


class TestSmallStudyFlag:
    def test_small_study_flagged(self):
        """Spec Edge Cases: N < 5 datasets must be explicitly flagged."""
        effects = [0.5, 0.6, 0.4]
        variances = [0.04] * 3
        for est in (estimate_fixed_effects, estimate_dersimonian_laird, estimate_reml):
            result = est(effects, variances)
            assert result.n_studies == 3
            assert result.small_study_flag is True

    def test_adequate_study_not_flagged(self):
        effects = [0.5, 0.6, 0.4, 0.7, 0.5]
        variances = [0.04] * 5
        result = estimate_fixed_effects(effects, variances)
        assert result.small_study_flag is False

    def test_flag_in_to_dict(self):
        result = estimate_fixed_effects([1.0, 2.0, 3.0], [1.0, 1.0, 1.0])
        d = result.to_dict()
        assert d["small_study_flag"] is True
        assert "q_statistic" in d and "i2" in d


class TestDispatcher:
    def test_apply_estimator_dispatch(self):
        effects = [0.5, 0.6, 0.4, 0.7, 0.5]
        variances = [0.04] * 5
        assert apply_estimator("fixed", effects, variances).tau2 == 0.0
        assert apply_estimator("dl", effects, variances).tau2 >= 0.0
        assert apply_estimator("reml", effects, variances).tau2 >= 0.0
        with pytest.raises(ValueError):
            apply_estimator("bogus", effects, variances)
