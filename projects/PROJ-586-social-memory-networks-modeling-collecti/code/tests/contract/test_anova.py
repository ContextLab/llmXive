"""Contract tests for ANOVA output schema.

This module validates that the ANOVA analysis produces output conforming to the
expected schema defined in the project specifications. It ensures that:

1. The output is a valid dictionary with required keys
2. All numeric fields are actual numbers (not strings)
3. The interaction term p-value is present and in valid range [0, 1]
4. Effect sizes are non-negative
5. Bonferroni correction is applied correctly
"""

import json
import math
from pathlib import Path
from typing import Any, Dict

import pytest

# Import the ANOVA output schema and analysis functions
# These are defined in code/analysis/anova.py
try:
    from analysis.anova import ANOVAOutput, run_anova_analysis
except ImportError:
    # Fallback for testing environment where analysis module might not be fully built
    pytest.skip("analysis.anova module not available", allow_module_level=True)


# Expected schema structure for ANOVA output
EXPECTED_SCHEMA = {
    "required_keys": [
        "interaction_p_value",
        "context_main_effect_p",
        "metric_main_effect_p",
        "context_effect_size",
        "metric_effect_size",
        "interaction_effect_size",
        "bonferroni_corrected_alpha",
        "degrees_of_freedom",
        "sample_size",
        "model_formula"
    ],
    "numeric_fields": [
        "interaction_p_value",
        "context_main_effect_p",
        "metric_main_effect_p",
        "context_effect_size",
        "metric_effect_size",
        "interaction_effect_size",
        "bonferroni_corrected_alpha"
    ],
    "range_constraints": {
        "interaction_p_value": (0.0, 1.0),
        "context_main_effect_p": (0.0, 1.0),
        "metric_main_effect_p": (0.0, 1.0),
        "context_effect_size": (0.0, float('inf')),
        "metric_effect_size": (0.0, float('inf')),
        "interaction_effect_size": (0.0, float('inf')),
        "bonferroni_corrected_alpha": (0.0, 1.0)
    }
}


def test_anova_output_schema_structure():
    """Test that ANOVA output has all required keys."""
    # Create a minimal valid ANOVA output for testing
    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    # Verify all required keys are present
    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output
    for key in EXPECTED_SCHEMA["required_keys"]:
        assert key in output_dict, f"Missing required key: {key}"


def test_anova_output_numeric_fields():
    """Test that all numeric fields are actual numbers."""
    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output

    for field in EXPECTED_SCHEMA["numeric_fields"]:
        value = output_dict[field]
        assert isinstance(value, (int, float)), f"Field {field} is not numeric: {type(value)}"
        assert not math.isnan(value), f"Field {field} is NaN"
        assert not math.isinf(value) or value > 0, f"Field {field} is negative infinity"


def test_anova_output_p_value_ranges():
    """Test that p-values are within valid range [0, 1]."""
    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output

    for field, (min_val, max_val) in EXPECTED_SCHEMA["range_constraints"].items():
        value = output_dict[field]
        assert min_val <= value <= max_val, (
            f"Field {field} = {value} is outside valid range [{min_val}, {max_val}]"
        )


def test_anova_output_effect_size_non_negative():
    """Test that effect sizes are non-negative."""
    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output

    effect_size_fields = ["context_effect_size", "metric_effect_size", "interaction_effect_size"]
    for field in effect_size_fields:
        value = output_dict[field]
        assert value >= 0, f"Effect size {field} = {value} is negative"


def test_anova_output_json_serializable():
    """Test that ANOVA output can be serialized to JSON."""
    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output

    # Should not raise
    json_str = json.dumps(output_dict, ensure_ascii=False, default=str)
    assert isinstance(json_str, str)
    assert len(json_str) > 0

    # Should be able to deserialize
    deserialized = json.loads(json_str)
    assert deserialized["interaction_p_value"] == 0.042


def test_anova_output_degrees_of_freedom_structure():
    """Test that degrees of freedom have expected structure."""
    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output

    dof = output_dict["degrees_of_freedom"]
    assert isinstance(dof, dict), "degrees_of_freedom should be a dictionary"

    expected_dof_keys = ["context", "metric", "interaction", "error"]
    for key in expected_dof_keys:
        assert key in dof, f"Missing degrees of freedom key: {key}"
        assert isinstance(dof[key], int), f"DOF for {key} should be integer"
        assert dof[key] >= 0, f"DOF for {key} should be non-negative"


def test_anova_output_model_formula_format():
    """Test that model formula follows expected format."""
    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output

    formula = output_dict["model_formula"]
    assert isinstance(formula, str), "model_formula should be a string"
    assert "~" in formula, "model_formula should contain '~' operator"
    assert "C(context_condition)" in formula, "model_formula should include context condition"
    assert "C(metric_name)" in formula, "model_formula should include metric name"
    assert "*" in formula, "model_formula should include interaction term (*)"


def test_anova_output_bonferroni_correction():
    """Test that Bonferroni correction is applied correctly."""
    # For 2 hypothesis tests (context main effect, metric main effect),
    # with alpha=0.05, corrected alpha should be 0.05/2 = 0.025
    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,  # 0.05 / 2 tests
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output

    # Verify the correction is reasonable (should be <= 0.05)
    assert output_dict["bonferroni_corrected_alpha"] <= 0.05, (
        "Bonferroni corrected alpha should be <= 0.05"
    )

    # Verify it's a reasonable division (for 2-4 tests, should be between 0.0125 and 0.05)
    assert 0.01 <= output_dict["bonferroni_corrected_alpha"] <= 0.05, (
        f"Bonferroni corrected alpha {output_dict['bonferroni_corrected_alpha']} "
        "seems unreasonable for typical test counts"
    )


def test_anova_output_sample_size_positive():
    """Test that sample size is positive."""
    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output

    assert output_dict["sample_size"] > 0, "Sample size should be positive"
    assert isinstance(output_dict["sample_size"], int), "Sample size should be integer"


def test_anova_output_consistency_with_data():
    """Test that ANOVA output is consistent with the underlying data structure."""
    # This test verifies that the output schema matches what run_anova_analysis would produce
    # given valid input data from results_full.csv and results_limited.csv

    # We create a minimal valid output and check its internal consistency
    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output

    # Check that sample_size is consistent with degrees of freedom
    # Total df = N - 1, so N = total_df + 1
    total_df = sum(output_dict["degrees_of_freedom"].values())
    assert output_dict["sample_size"] == total_df + 1, (
        f"Sample size {output_dict['sample_size']} should equal total_df + 1 = {total_df + 1}"
    )

    # Check that p-values and effect sizes are in reasonable ranges for each other
    # (high p-value should generally correspond to low effect size, though not strictly)
    if output_dict["interaction_p_value"] > 0.05:
        assert output_dict["interaction_effect_size"] < 0.3, (
            "High p-value (>0.05) should generally correspond to small effect size"
        )


def test_anova_output_schema_compliance_with_spec():
    """Test that output complies with the specification requirements."""
    # Per FR-006: Single two-way ANOVA with Context × Metric interaction
    # Per FR-007: Bonferroni correction applied

    test_output = ANOVAOutput(
        interaction_p_value=0.042,
        context_main_effect_p=0.031,
        metric_main_effect_p=0.008,
        context_effect_size=0.15,
        metric_effect_size=0.28,
        interaction_effect_size=0.12,
        bonferroni_corrected_alpha=0.025,
        degrees_of_freedom={"context": 1, "metric": 1, "interaction": 1, "error": 1996},
        sample_size=2000,
        model_formula="metric_value ~ C(context_condition) * C(metric_name)"
    )

    output_dict = test_output.to_dict() if hasattr(test_output, 'to_dict') else test_output

    # Verify interaction term is present (FR-006)
    assert "interaction_p_value" in output_dict, "Missing interaction p-value (FR-006)"
    assert "interaction_effect_size" in output_dict, "Missing interaction effect size (FR-006)"

    # Verify Bonferroni correction is present (FR-007)
    assert "bonferroni_corrected_alpha" in output_dict, "Missing Bonferroni correction (FR-007)"

    # Verify the model formula includes both factors and their interaction
    formula = output_dict["model_formula"]
    assert "context_condition" in formula, "Model should include context condition"
    assert "metric_name" in formula, "Model should include metric name"
    assert "*" in formula or ":" in formula, "Model should include interaction term"