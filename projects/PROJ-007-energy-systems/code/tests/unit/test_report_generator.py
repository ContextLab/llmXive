"""
Tests for the report generator module.

These tests verify that:
1. Causal and scaling sections are generated separately
2. Scaling section contains required disclaimers
3. No cross-contamination between sections
4. Report structure validation works correctly
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from src.report.generator import (
    generate_causal_section,
    generate_scaling_section,
    generate_full_report,
    validate_report_structure,
    ReportGenerationError
)
from src.models.output import AnalysisResult


@pytest.fixture
def sample_causal_result():
    """Create a sample AnalysisResult for testing."""
    return AnalysisResult(
        ATT=0.15,
        ATT_se=0.05,
        ATT_ci_95=[0.05, 0.25],
        ATT_p_value=0.003,
        caliper_used=0.05,
        covariates_used=["income", "housing_type", "location"],
        balance_status="PASS",
        max_smd=0.08,
        placebo_test_performed=True,
        placebo_p_value=0.45,
        placebo_significant=False,
        sensitivity_data=[
            {"caliper": 0.05, "ATT": 0.15, "p_value": 0.003},
            {"caliper": 0.10, "ATT": 0.14, "p_value": 0.005}
        ]
    )


@pytest.fixture
def sample_scaling_report():
    """Create a sample scaling report for testing."""
    return {
        "exponent": 0.82,
        "exponent_ci": [0.78, 0.86],
        "r_squared": 0.75,
        "n_tracts": 150,
        "comparison_interpretation": "Slightly below universal exponent of 0.85",
        "findings": [
            "Energy consumption scales sublinearly with population",
            "Low-income communities show similar scaling patterns to cities"
        ]
    }


class TestGenerateCausalSection:
    """Tests for generate_causal_section function."""

    def test_causal_section_contains_required_fields(self, sample_causal_result):
        """Verify causal section contains all required fields."""
        section = generate_causal_section(sample_causal_result)

        assert "section_title" in section
        assert section["section_title"] == "Causal Inference Results"
        assert "methodology" in section
        assert "balance_validation" in section
        assert "causal_estimate" in section
        assert "sensitivity_analysis" in section
        assert "limitations" in section
        assert "disclaimer" in section

    def test_causal_section_excludes_scaling_results(self, sample_causal_result):
        """Verify causal section does NOT contain scaling law results."""
        section = generate_causal_section(sample_causal_result)
        section_text = json.dumps(section).lower()

        assert "scaling exponent" not in section_text
        assert "beta" not in section_text
        assert "universal exponent" not in section_text
        assert "sublinear" not in section_text

    def test_causal_section_with_missing_result_raises_error(self):
        """Verify None result raises ReportGenerationError."""
        with pytest.raises(ReportGenerationError, match="cannot be None"):
            generate_causal_section(None)

    def test_causal_section_with_missing_att_raises_error(self):
        """Verify missing ATT raises ReportGenerationError."""
        result = AnalysisResult(
            ATT=None,
            ATT_se=0.05,
            ATT_ci_95=[0.05, 0.25],
            ATT_p_value=0.003,
            caliper_used=0.05,
            covariates_used=["income"],
            balance_status="PASS",
            max_smd=0.08,
            placebo_test_performed=True,
            placebo_p_value=0.45,
            placebo_significant=False,
            sensitivity_data=[]
        )
        with pytest.raises(ReportGenerationError, match="ATT is missing"):
            generate_causal_section(result)


class TestGenerateScalingSection:
    """Tests for generate_scaling_section function."""

    def test_scaling_section_contains_required_disclaimers(self, sample_scaling_report):
        """Verify scaling section contains required disclaimers."""
        section = generate_scaling_section(sample_scaling_report)

        assert "strict_disclaimers" in section
        disclaimers = section["strict_disclaimers"]

        # Check for key disclaimer phrases
        disclaimer_text = " ".join(disclaimers).lower()
        assert "descriptive only" in disclaimer_text
        assert "causal" in disclaimer_text
        assert "not evidence" in disclaimer_text

    def test_scaling_section_excludes_causal_results(self, sample_scaling_report):
        """Verify scaling section does NOT contain causal inference results."""
        section = generate_scaling_section(sample_scaling_report)
        section_text = json.dumps(section).lower()

        assert "att" not in section_text
        assert "treatment effect" not in section_text
        assert "propensity score" not in section_text
        assert "matching" not in section_text

    def test_scaling_section_with_missing_report_raises_error(self):
        """Verify None report raises ReportGenerationError."""
        with pytest.raises(ReportGenerationError, match="cannot be None"):
            generate_scaling_section(None)

    def test_scaling_section_includes_methodology_separation(self, sample_scaling_report):
        """Verify scaling section includes methodology separation statement."""
        section = generate_scaling_section(sample_scaling_report)

        assert "methodology_separation_statement" in section
        separation_text = section["methodology_separation_statement"].lower()
        assert "separate" in separation_text
        assert "causal" in separation_text


class TestGenerateFullReport:
    """Tests for generate_full_report function."""

    def test_full_report_contains_separated_sections(self, sample_causal_result, sample_scaling_report):
        """Verify full report contains both separated sections."""
        report = generate_full_report(
            causal_result=sample_causal_result,
            scaling_report=sample_scaling_report
        )

        assert "causal_inference" in report
        assert "descriptive_scaling_law" in report

        # Verify sections are distinct
        assert report["causal_inference"]["section_title"] == "Causal Inference Results"
        assert report["descriptive_scaling_law"]["section_title"] == "Descriptive Scaling Law Analysis"

    def test_full_report_includes_separation_statement(self, sample_causal_result, sample_scaling_report):
        """Verify full report includes methodological separation statement."""
        report = generate_full_report(
            causal_result=sample_causal_result,
            scaling_report=sample_scaling_report
        )

        assert "methodological_separation_statement" in report
        statement = report["methodological_separation_statement"].lower()
        assert "separate" in statement
        assert "causal" in statement
        assert "descriptive" in statement

    def test_full_report_with_missing_causal_result(self, sample_scaling_report):
        """Verify report handles missing causal result gracefully."""
        report = generate_full_report(
            causal_result=None,
            scaling_report=sample_scaling_report
        )

        assert "causal_inference" in report
        assert report["causal_inference"]["status"] == "NOT_AVAILABLE"
        assert "descriptive_scaling_law" in report

    def test_full_report_with_missing_scaling_report(self, sample_causal_result):
        """Verify report handles missing scaling report gracefully."""
        report = generate_full_report(
            causal_result=sample_causal_result,
            scaling_report=None
        )

        assert "descriptive_scaling_law" in report
        assert report["descriptive_scaling_law"]["status"] == "NOT_AVAILABLE"
        assert "causal_inference" in report

    def test_full_report_saves_to_file(self, sample_causal_result, sample_scaling_report, tmp_path):
        """Verify report can be saved to file."""
        output_path = tmp_path / "test_report.json"
        report = generate_full_report(
            causal_result=sample_causal_result,
            scaling_report=sample_scaling_report,
            output_path=output_path
        )

        assert output_path.exists()
        with open(output_path, 'r') as f:
            saved_report = json.load(f)

        assert saved_report["causal_inference"]["section_title"] == "Causal Inference Results"
        assert saved_report["descriptive_scaling_law"]["section_title"] == "Descriptive Scaling Law Analysis"


class TestValidateReportStructure:
    """Tests for validate_report_structure function."""

    def test_valid_report_returns_true(self, sample_causal_result, sample_scaling_report):
        """Verify valid report passes validation."""
        report = generate_full_report(
            causal_result=sample_causal_result,
            scaling_report=sample_scaling_report
        )

        assert validate_report_structure(report) is True

    def test_missing_causal_section_returns_false(self, sample_scaling_report):
        """Verify report without causal section fails validation."""
        report = generate_full_report(
            causal_result=None,
            scaling_report=sample_scaling_report
        )
        # Remove the status marker to simulate a truly missing section
        del report["causal_inference"]

        assert validate_report_structure(report) is False

    def test_missing_scaling_section_returns_false(self, sample_causal_result):
        """Verify report without scaling section fails validation."""
        report = generate_full_report(
            causal_result=sample_causal_result,
            scaling_report=None
        )
        # Remove the status marker to simulate a truly missing section
        del report["descriptive_scaling_law"]

        assert validate_report_structure(report) is False

    def test_cross_contamination_detection(self, sample_causal_result, sample_scaling_report):
        """Verify cross-contamination between sections is detected."""
        report = generate_full_report(
            causal_result=sample_causal_result,
            scaling_report=sample_scaling_report
        )

        # Inject scaling result into causal section
        report["causal_inference"]["scaling_exponent"] = 0.82

        assert validate_report_structure(report) is False

    def test_missing_disclaimers_detection(self, sample_causal_result):
        """Verify missing disclaimers in scaling section are detected."""
        report = generate_full_report(
            causal_result=sample_causal_result,
            scaling_report={"exponent": 0.82}  # Missing disclaimers
        )

        assert validate_report_structure(report) is False