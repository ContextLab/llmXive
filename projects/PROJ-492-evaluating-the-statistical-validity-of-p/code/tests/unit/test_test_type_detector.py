"""
Unit tests for outcome-type detection heuristics.
"""
import pytest
from code.src.audit.test_type_detector import (
    detect_outcome_type,
    detect_outcome_type_from_summaries,
    OUTCOME_BINARY,
    OUTCOME_CONTINUOUS,
    OUTCOME_UNKNOWN
)

class TestOutcomeTypeDetection:
    """Test suite for outcome type detection heuristics."""

    def test_binary_with_conversion_rates(self):
        """Binary outcome detected when conversion rates are present."""
        summary = {
            "baseline_conversion": 0.05,
            "treatment_conversion": 0.07,
            "n_baseline": 1000,
            "n_treatment": 1000
        }
        outcome_type, note = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_BINARY
        assert "Conversion" in note or "rate" in note.lower()

    def test_continuous_with_means(self):
        """Continuous outcome detected when means and stds are present."""
        summary = {
            "mean_control": 10.5,
            "mean_treatment": 12.3,
            "std_control": 2.1,
            "std_treatment": 2.5,
            "n_control": 50,
            "n_treatment": 50
        }
        outcome_type, note = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_CONTINUOUS
        assert "Mean" in note or "standard deviation" in note.lower()

    def test_explicit_binary_type(self):
        """Binary outcome detected from explicit type indicator."""
        summary = {
            "outcome_type": "binary",
            "p_value": 0.03
        }
        outcome_type, note = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_BINARY

    def test_explicit_continuous_type(self):
        """Continuous outcome detected from explicit type indicator."""
        summary = {
            "metric_type": "continuous",
            "test_type": "t-test"
        }
        outcome_type, note = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_CONTINUOUS

    def test_z_test_indicates_binary(self):
        """Z-test indication leads to binary classification."""
        summary = {
            "test_type": "two-proportion z-test",
            "effect_size": 0.02
        }
        outcome_type, note = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_BINARY

    def test_welch_t_test_indicates_continuous(self):
        """Welch t-test indication leads to continuous classification."""
        summary = {
            "test_type": "Welch's t-test",
            "effect_size": 1.5
        }
        outcome_type, note = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_CONTINUOUS

    def test_unknown_type_when_no_indicators(self):
        """Unknown type returned when no indicators are present."""
        summary = {
            "p_value": 0.04
        }
        outcome_type, note = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_UNKNOWN

    def test_invalid_summary_format(self):
        """Unknown type returned for invalid summary format."""
        outcome_type, note = detect_outcome_type("not a dict")
        assert outcome_type == OUTCOME_UNKNOWN

    def test_null_summary(self):
        """Unknown type returned for None summary."""
        outcome_type, note = detect_outcome_type(None)
        assert outcome_type == OUTCOME_UNKNOWN

    def test_detection_statistics(self):
        """Test detection statistics across multiple summaries."""
        summaries = [
            {"baseline_conversion": 0.05},
            {"mean_control": 10.0},
            {"outcome_type": "binary"},
            {"p_value": 0.05}
        ]
        results = detect_outcome_type_from_summaries(summaries)
        
        assert results['total_count'] == 4
        assert results['binary_count'] == 2
        assert results['continuous_count'] == 1
        assert results['unknown_count'] == 1
        assert len(results['detections']) == 4

    def test_multiple_conversion_field_variants(self):
        """Test various conversion field names trigger binary detection."""
        test_cases = [
            {"baseline_conversion": 0.05},
            {"treatment_conversion": 0.07},
            {"control_conversion": 0.05, "variant_conversion": 0.07},
            {"baseline_rate": 0.05},
            {"control_rate": 0.05},
            {"baseline_conversions": 50, "treatment_conversions": 70}
        ]
        
        for summary in test_cases:
            outcome_type, _ = detect_outcome_type(summary)
            assert outcome_type == OUTCOME_BINARY, f"Failed for {summary}"

    def test_multiple_continuous_field_variants(self):
        """Test various mean/std field names trigger continuous detection."""
        test_cases = [
            {"mean_control": 10.0, "mean_treatment": 12.0},
            {"mean_baseline": 10.0, "mean_variant": 12.0},
            {"std_control": 1.0, "std_treatment": 1.5},
            {"standard_deviation_control": 1.0, "standard_deviation_treatment": 1.5}
        ]
        
        for summary in test_cases:
            outcome_type, _ = detect_outcome_type(summary)
            assert outcome_type == OUTCOME_CONTINUOUS, f"Failed for {summary}"

    def test_effect_size_type_proportion(self):
        """Effect size type 'proportion' triggers binary detection."""
        summary = {
            "effect_size_type": "risk difference",
            "effect_size": 0.02
        }
        outcome_type, _ = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_BINARY

    def test_effect_size_type_mean(self):
        """Effect size type 'mean difference' with value > 1 triggers continuous."""
        summary = {
            "effect_size_type": "mean difference",
            "effect_size": 2.5
        }
        outcome_type, _ = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_CONTINUOUS

    def test_effect_size_in_range_0_to_1(self):
        """Effect size in [0,1] range with large N suggests binary."""
        summary = {
            "n_control": 5000,
            "n_treatment": 5000,
            "effect_size": 0.03,
            "p_value": 0.01
        }
        outcome_type, _ = detect_outcome_type(summary)
        # Should be binary due to small effect size with large N
        assert outcome_type == OUTCOME_BINARY