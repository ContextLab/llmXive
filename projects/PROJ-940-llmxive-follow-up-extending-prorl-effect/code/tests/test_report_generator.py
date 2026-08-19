"""
Tests for the Report Generator module (T032).
"""
import json
import os
import tempfile
import pytest
from pathlib import Path

# We need to mock the file paths used in the module
# Since the module uses hardcoded PROJECT_ROOT relative to itself,
# we will test the logic by creating temporary files in a temp directory
# and patching the paths or by directly testing the rendering functions.

# Import the rendering functions directly to test logic without file I/O
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from src.report_generator import (
    render_sc005_section,
    render_metrics_comparison_section,
    render_statistical_significance_section,
    render_sensitivity_analysis_section,
    format_table
)


class TestFormatTable:
    def test_format_table_empty_rows(self):
        headers = ["A", "B"]
        result = format_table(headers, [])
        assert "*No data available.*" in result

    def test_format_table_basic(self):
        headers = ["Name", "Value"]
        rows = [["Item1", 10], ["Item2", 20]]
        result = format_table(headers, rows)
        assert "Name" in result
        assert "Item1" in result
        assert "10" in result
        assert "|" in result


class TestRenderSC005:
    def test_render_missing_data(self):
        result = render_sc005_section(None)
        assert "Not executed or file missing" in result

    def test_render_pass_status(self):
        data = {
            "status": "pass",
            "mean_absolute_difference": 0.05,
            "threshold": 0.01,
            "timestamp": "2023-01-01"
        }
        result = render_sc005_section(data)
        assert "PASS" in result
        assert "statistically measurable impact" in result
        assert "0.05" in result

    def test_render_fail_status(self):
        data = {
            "status": "fail",
            "mean_absolute_difference": 0.005,
            "threshold": 0.01
        }
        result = render_sc005_section(data)
        assert "FAIL" in result
        assert "below the required threshold" in result


class TestRenderMetricsComparison:
    def test_render_missing_data(self):
        result = render_metrics_comparison_section(None)
        assert "missing" in result.lower()

    def test_render_comparison(self):
        data = {
            "greedy": {
                "precision_at_k": 0.4,
                "recall_at_k": 0.3,
                "diversity": 0.5,
                "coverage": 0.8
            },
            "prorl": {
                "precision_at_k": 0.45,
                "recall_at_k": 0.35,
                "diversity": 0.6,
                "coverage": 0.85
            }
        }
        result = render_metrics_comparison_section(data)
        assert "Precision@K" in result
        assert "0.4000" in result
        assert "0.4500" in result
        assert "+" in result  # Improvement indicator


class TestRenderStatisticalSignificance:
    def test_render_missing_data(self):
        result = render_statistical_significance_section(None)
        assert "missing" in result.lower()

    def test_render_significant(self):
        data = {
            "test_method": "Wilcoxon",
            "p_value": 0.001,
            "is_significant": True,
            "confidence_interval": "[0.01, 0.05]"
        }
        result = render_statistical_significance_section(data)
        assert "Wilcoxon" in result
        assert "0.001" in result
        assert "statistically significant" in result

    def test_render_not_significant(self):
        data = {
            "test_method": "T-test",
            "p_value": 0.15,
            "is_significant": False
        }
        result = render_statistical_significance_section(data)
        assert "not statistically significant" in result


class TestRenderSensitivityAnalysis:
    def test_render_missing_data(self):
        result = render_sensitivity_analysis_section(None)
        assert "missing" in result.lower()

    def test_render_path_length_sweep(self):
        data = {
            "path_length_sweep": [
                {"length": 3, "precision": 0.3, "diversity": 0.5, "coverage": 0.7},
                {"length": 5, "precision": 0.35, "diversity": 0.6, "coverage": 0.8}
            ],
            "summary": {
                "optimal_path_length": 5,
                "robustness_note": "Stable across range"
            }
        }
        result = render_sensitivity_analysis_section(data)
        assert "Path Length (L)" in result
        assert "3" in result
        assert "5" in result
        assert "Optimal Path Length" in result
        assert "5" in result  # From summary

    def test_render_threshold_sweep(self):
        data = {
            "sim_threshold_sweep": [
                {"threshold": 0.01, "precision": 0.4, "diversity": 0.5, "coverage": 0.8},
                {"threshold": 0.1, "precision": 0.42, "diversity": 0.55, "coverage": 0.75}
            ]
        }
        result = render_sensitivity_analysis_section(data)
        assert "Similarity Threshold Sensitivity" in result
        assert "0.01" in result
        assert "0.1" in result