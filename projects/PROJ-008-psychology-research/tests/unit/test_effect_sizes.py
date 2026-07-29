"""
Unit tests for Hedges' g calculation accuracy.

Tests verify that the calculation matches manual computations
within a tolerance of 0.001 as specified in T022.
"""
import pytest
import math
from code.analysis.effect_sizes import calculate_hedges_g, calculate_effect_sizes_from_studies
from code.data.models import Study, InterventionGroup, ControlGroup


class TestHedgesGCalculation:
    """Test suite for Hedges' g calculation accuracy."""

    def test_simple_manual_calculation(self):
        """
        Test against a simple manual calculation.

        Example:
            Group 1: n=10, mean=50, sd=10
            Group 2: n=12, mean=45, sd=10

        Manual calculation:
            Pooled SD = sqrt(((9*100) + (11*100)) / 20) = sqrt(100) = 10
            Cohen's d = (50-45)/10 = 0.5
            J = 1 - (3/(4*20-1)) = 1 - (3/79) = 0.962
            Hedges' g = 0.5 * 0.962 = 0.481
        """
        n1, n2 = 10, 12
        mean1, mean2 = 50.0, 45.0
        sd1, sd2 = 10.0, 10.0

        g, variance, se, ci_low, ci_high, j = calculate_hedges_g(n1, n2, mean1, mean2, sd1, sd2)

        # Expected values
        expected_g = 0.4810126582278481
        expected_variance = 0.18174603174603175
        expected_se = 0.4263168208774193

        # Tolerance: 0.001 as per task specification
        tolerance = 0.001

        assert abs(g - expected_g) < tolerance, f"g={g}, expected={expected_g}"
        assert abs(variance - expected_variance) < tolerance, f"variance={variance}, expected={expected_variance}"
        assert abs(se - expected_se) < tolerance, f"se={se}, expected={expected_se}"

    def test_equal_sample_sizes(self):
        """Test with equal sample sizes."""
        n1, n2 = 20, 20
        mean1, mean2 = 100.0, 90.0
        sd1, sd2 = 15.0, 15.0

        g, variance, se, ci_low, ci_high, j = calculate_hedges_g(n1, n2, mean1, mean2, sd1, sd2)

        # Pooled SD = 15
        # Cohen's d = 10/15 = 0.6667
        # J = 1 - 3/(4*38-1) = 1 - 3/151 = 0.9801
        # Hedges' g = 0.6667 * 0.9801 = 0.6534

        expected_g = 0.6534013605442177
        tolerance = 0.001

        assert abs(g - expected_g) < tolerance

    def test_small_sample_correction(self):
        """Verify that small-sample correction is applied correctly."""
        # Very small samples
        n1, n2 = 5, 5
        mean1, mean2 = 10.0, 8.0
        sd1, sd2 = 2.0, 2.0

        g, variance, se, ci_low, ci_high, j = calculate_hedges_g(n1, n2, mean1, mean2, sd1, sd2)

        # Without correction, Cohen's d = 1.0
        # With correction, Hedges' g should be slightly less than 1.0
        assert g < 1.0, "Small-sample correction should reduce the effect size"
        assert g > 0.9, "Correction should be minimal for this sample size"

    def test_invalid_input_positive_sd(self):
        """Test that non-positive SD raises ValueError."""
        with pytest.raises(ValueError):
            calculate_hedges_g(10, 10, 50.0, 45.0, 0.0, 10.0)

    def test_invalid_input_positive_n(self):
        """Test that non-positive sample size raises ValueError."""
        with pytest.raises(ValueError):
            calculate_hedges_g(0, 10, 50.0, 45.0, 10.0, 10.0)

    def test_confidence_interval_bounds(self):
        """Test that CI bounds are correctly calculated."""
        g, variance, se, ci_low, ci_high, j = calculate_hedges_g(20, 20, 100.0, 90.0, 15.0, 15.0)

        # CI should be symmetric around g
        assert ci_low < g < ci_high
        assert abs((g - ci_low) - (ci_high - g)) < 0.0001

    def test_large_effect_size(self):
        """Test with a large effect size."""
        g, variance, se, ci_low, ci_high, j = calculate_hedges_g(30, 30, 100.0, 70.0, 10.0, 10.0)

        # Cohen's d = 3.0, Hedges' g should be close to 3.0
        assert g > 2.5
        assert g < 3.1

    def test_zero_effect_size(self):
        """Test when means are equal."""
        g, variance, se, ci_low, ci_high, j = calculate_hedges_g(20, 20, 50.0, 50.0, 10.0, 10.0)

        assert abs(g) < 0.001
        assert ci_low < 0 < ci_high

class TestEffectSizeFromStudy:
    """Test effect size calculation from Study objects."""

    def test_process_valid_study(self):
        """Test processing a valid Study object."""
        study = Study(
            study_id="TEST-001",
            intervention_group=InterventionGroup(n=20, mean=100.0, sd=15.0),
            control_group=ControlGroup(n=20, mean=90.0, sd=15.0),
            population="ASD",
            age_range_min=8,
            age_range_max=12,
            outcome_measure="Social Skills Rating",
            study_type="RCT",
            delivery_format="Group",
            mindfulness_component="Mindfulness-Based Stress Reduction"
        )

        results = calculate_effect_sizes_from_studies([study])

        assert len(results) == 1
        assert results[0].study_id == "TEST-001"
        assert abs(results[0].hedges_g - 0.6534) < 0.001

    def test_skip_study_with_missing_data(self):
        """Test that studies with missing data are skipped."""
        study = Study(
            study_id="TEST-002",
            intervention_group=InterventionGroup(n=20, mean=100.0, sd=15.0),
            control_group=ControlGroup(n=0, mean=90.0, sd=15.0),  # n=0
            population="ASD",
            age_range_min=8,
            age_range_max=12,
            outcome_measure="Social Skills Rating",
            study_type="RCT",
            delivery_format="Group",
            mindfulness_component="Mindfulness-Based Stress Reduction"
        )

        results = calculate_effect_sizes_from_studies([study])

        assert len(results) == 0

    def test_multiple_studies(self):
        """Test processing multiple studies."""
        study1 = Study(
            study_id="TEST-001",
            intervention_group=InterventionGroup(n=20, mean=100.0, sd=15.0),
            control_group=ControlGroup(n=20, mean=90.0, sd=15.0),
            population="ASD",
            age_range_min=8,
            age_range_max=12,
            outcome_measure="Social Skills Rating",
            study_type="RCT",
            delivery_format="Group",
            mindfulness_component="Mindfulness-Based Stress Reduction"
        )

        study2 = Study(
            study_id="TEST-002",
            intervention_group=InterventionGroup(n=25, mean=80.0, sd=10.0),
            control_group=ControlGroup(n=25, mean=75.0, sd=10.0),
            population="ASD",
            age_range_min=8,
            age_range_max=12,
            outcome_measure="Social Skills Rating",
            study_type="RCT",
            delivery_format="Individual",
            mindfulness_component="Mindfulness-Based Cognitive Therapy"
        )

        results = calculate_effect_sizes_from_studies([study1, study2])

        assert len(results) == 2
        assert results[0].study_id == "TEST-001"
        assert results[1].study_id == "TEST-002"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])