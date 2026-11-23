"""
Unit tests for report generation functionality.

Tests the conditional phrasing logic in report_generator.py
to ensure correct causal/statistical language based on p-values.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from report_generator import generate_markdown_report, load_statistical_results


class TestReportGeneration:
    """Test cases for report generation."""

    def test_load_statistical_results_from_list(self):
        """Test loading statistical results from a JSON list."""
        test_data = [
            {
                "test_type": "anova",
                "f_statistic": 15.5,
                "p_value": 0.001,
                "corrected_p_value": 0.003,
                "conclusion": "Significant",
                "correction_method": "Bonferroni"
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            results = load_statistical_results(temp_path)
            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0]['test_type'] == 'anova'
        finally:
            os.unlink(temp_path)

    def test_load_statistical_results_from_dict(self):
        """Test loading statistical results from a JSON dict with 'results' key."""
        test_data = {
            "results": [
                {
                    "test_type": "pairwise_t_test",
                    "t_statistic": 3.2,
                    "p_value": 0.002,
                    "corrected_p_value": 0.006
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            results = load_statistical_results(temp_path)
            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0]['test_type'] == 'pairwise_t_test'
        finally:
            os.unlink(temp_path)

    def test_conditional_causal_language_significant(self):
        """
        Test that the report includes 'causal regarding the effect of entropy'
        when corrected p-value < 0.05.
        """
        test_results = [
            {
                "test_type": "anova",
                "f_statistic": 25.0,
                "p_value": 0.0001,
                "corrected_p_value": 0.0003,
                "conclusion": "Significant",
                "correction_method": "Bonferroni"
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.md')

            generate_markdown_report(test_results, output_path)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            # Assert the causal phrase is present
            assert "causal regarding the effect of entropy on performance" in content
            # Assert the non-significant phrase is NOT present
            assert "no statistically significant effect detected" not in content

    def test_conditional_causal_language_not_significant(self):
        """
        Test that the report includes 'no statistically significant effect detected'
        when corrected p-value >= 0.05.
        """
        test_results = [
            {
                "test_type": "anova",
                "f_statistic": 1.5,
                "p_value": 0.25,
                "corrected_p_value": 0.75,
                "conclusion": "Not Significant",
                "correction_method": "Bonferroni"
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.md')

            generate_markdown_report(test_results, output_path)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            # Assert the non-significant phrase is present
            assert "no statistically significant effect detected" in content
            # Assert the causal phrase is NOT present
            assert "causal regarding the effect of entropy on performance" not in content

    def test_conditional_causal_language_boundary(self):
        """
        Test boundary case where corrected p-value equals threshold (0.05).
        Should result in 'no statistically significant effect detected'.
        """
        test_results = [
            {
                "test_type": "anova",
                "f_statistic": 3.0,
                "p_value": 0.05,
                "corrected_p_value": 0.05,
                "conclusion": "Borderline",
                "correction_method": "Bonferroni"
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.md')

            generate_markdown_report(test_results, output_path)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            # At exactly 0.05, should NOT be significant
            assert "no statistically significant effect detected" in content
            assert "causal regarding the effect of entropy on performance" not in content

    def test_report_structure(self):
        """Test that the generated report contains expected sections."""
        test_results = [
            {
                "test_type": "anova",
                "f_statistic": 10.0,
                "p_value": 0.01,
                "corrected_p_value": 0.03,
                "conclusion": "Significant",
                "correction_method": "Bonferroni"
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.md')

            generate_markdown_report(test_results, output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for expected sections
            assert "# Research Report:" in content
            assert "## Executive Summary" in content
            assert "## Methodology" in content
            assert "## Statistical Results" in content
            assert "### ANOVA Test" in content
            assert "## Conclusion" in content

    def test_report_generation_with_missing_file(self):
        """Test that FileNotFoundError is raised for missing input file."""
        with pytest.raises(FileNotFoundError):
            load_statistical_results("nonexistent_file.json")

    def test_report_with_multiple_test_types(self):
        """Test report generation with multiple test types."""
        test_results = [
            {
                "test_type": "anova",
                "f_statistic": 20.0,
                "p_value": 0.001,
                "corrected_p_value": 0.003,
                "conclusion": "Significant",
                "correction_method": "Bonferroni"
            },
            {
                "test_type": "pairwise_t_test",
                "comparison": "High vs Low",
                "t_statistic": 4.5,
                "p_value": 0.0005,
                "corrected_p_value": 0.0015
            },
            {
                "test_type": "bonferroni_correction",
                "test_type_detail": "anova",
                "correction_method": "Bonferroni",
                "n_comparisons": 3
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.md')

            generate_markdown_report(test_results, output_path)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            # Should include all test types
            assert "ANOVA Test" in content
            assert "Pairwise t-tests" in content
            assert "Bonferroni Correction Summary" in content
            assert "causal regarding the effect of entropy on performance" in content
