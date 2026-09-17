"""
Unit tests for the report generation module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.report import load_spot_check_results, assemble_report


class TestLoadSpotCheckResults:
    """Tests for load_spot_check_results function."""

    def test_load_valid_spot_check_results(self, tmp_path):
        """Test loading valid spot-check results CSV."""
        # Create a temporary validation report
        csv_content = "misclassified_AI,total_sample_size\n5,50\n"
        csv_file = tmp_path / "validation_report.csv"
        csv_file.write_text(csv_content)

        # Load results
        results = load_spot_check_results(str(csv_file))

        # Verify calculations
        assert results['misclassified_ai'] == 5
        assert results['total_sample_size'] == 50
        assert abs(results['false_negative_rate'] - 0.10) < 1e-6
        assert results['filepath'] == str(csv_file)

    def test_load_empty_file(self, tmp_path):
        """Test loading an empty CSV file."""
        csv_file = tmp_path / "validation_report.csv"
        csv_file.write_text("")

        with pytest.raises(ValueError, match="empty or has no data rows"):
            load_spot_check_results(str(csv_file))

    def test_load_header_only(self, tmp_path):
        """Test loading a CSV with only headers."""
        csv_file = tmp_path / "validation_report.csv"
        csv_file.write_text("misclassified_AI,total_sample_size\n")

        with pytest.raises(ValueError, match="Total sample size is zero"):
            load_spot_check_results(str(csv_file))

    def test_load_invalid_values(self, tmp_path):
        """Test loading CSV with invalid numeric values."""
        csv_content = "misclassified_AI,total_sample_size\nabc,50\n5,xyz\n"
        csv_file = tmp_path / "validation_report.csv"
        csv_file.write_text(csv_content)

        # Should skip invalid rows and calculate with valid ones
        results = load_spot_check_results(str(csv_file))
        assert results['total_sample_size'] == 0  # All rows invalid
        with pytest.raises(ValueError, match="Total sample size is zero"):
            load_spot_check_results(str(csv_file))

    def test_file_not_found(self, tmp_path):
        """Test loading a non-existent file."""
        with pytest.raises(FileNotFoundError, match="not found"):
            load_spot_check_results(str(tmp_path / "nonexistent.csv"))


class TestAssembleReport:
    """Tests for assemble_report function."""

    def test_assemble_report_with_significant_results(self, tmp_path):
        """Test assembling report with significant p-value."""
        # Create temporary files
        stats_file = tmp_path / "statistical_results.json"
        stats_data = {
            "p_value": 0.03,
            "u_statistic": 1234.5,
            "effect_size": 0.45,
            "sample_sizes": {"ai_group": 100, "non_ai_group": 150},
            "descriptive_statistics": {
                "ai_group": {"median": 24.5},
                "non_ai_group": {"median": 48.2}
            }
        }
        stats_file.write_text(json.dumps(stats_data))

        spot_check_results = {
            "false_negative_rate": 0.08,
            "misclassified_ai": 4,
            "total_sample_size": 50
        }

        output_file = tmp_path / "final_report.md"

        # Assemble report
        report = assemble_report(
            statistical_results_path=str(stats_file),
            spot_check_results=spot_check_results,
            output_path=str(output_file)
        )

        # Verify report content
        assert "Statistical Test Results" in report
        assert "P-value: 0.030000" in report
        assert "Significant difference" in report
        assert "False-Negative Rate: 0.0800" in report
        assert "within acceptable limits" in report
        assert output_file.exists()

    def test_assemble_report_with_non_significant_results(self, tmp_path):
        """Test assembling report with non-significant p-value."""
        stats_file = tmp_path / "statistical_results.json"
        stats_data = {
            "p_value": 0.15,
            "u_statistic": 987.6,
            "effect_size": 0.12,
            "sample_sizes": {"ai_group": 80, "non_ai_group": 120},
            "descriptive_statistics": {
                "ai_group": {"median": 30.0},
                "non_ai_group": {"median": 32.5}
            }
        }
        stats_file.write_text(json.dumps(stats_data))

        spot_check_results = {
            "false_negative_rate": 0.05,
            "misclassified_ai": 2,
            "total_sample_size": 40
        }

        output_file = tmp_path / "final_report.md"

        report = assemble_report(
            statistical_results_path=str(stats_file),
            spot_check_results=spot_check_results,
            output_path=str(output_file)
        )

        assert "No statistically significant difference" in report
        assert "within acceptable limits" in report

    def test_assemble_report_with_high_false_negative_rate(self, tmp_path):
        """Test assembling report with high false-negative rate (>10%)."""
        stats_file = tmp_path / "statistical_results.json"
        stats_data = {
            "p_value": 0.04,
            "u_statistic": 1500.0,
            "effect_size": 0.35,
            "sample_sizes": {"ai_group": 90, "non_ai_group": 110},
            "descriptive_statistics": {
                "ai_group": {"median": 20.0},
                "non_ai_group": {"median": 45.0}
            }
        }
        stats_file.write_text(json.dumps(stats_data))

        spot_check_results = {
            "false_negative_rate": 0.12,  # 12% > 10%
            "misclassified_ai": 6,
            "total_sample_size": 50
        }

        output_file = tmp_path / "final_report.md"

        report = assemble_report(
            statistical_results_path=str(stats_file),
            spot_check_results=spot_check_results,
            output_path=str(output_file)
        )

        assert "False-negative rate exceeds 10% threshold" in report
        assert "Limitation:" in report

    def test_assemble_report_with_boxplot(self, tmp_path):
        """Test assembling report with boxplot visualization."""
        stats_file = tmp_path / "statistical_results.json"
        stats_data = {
            "p_value": 0.02,
            "u_statistic": 1100.0,
            "effect_size": 0.50,
            "sample_sizes": {"ai_group": 100, "non_ai_group": 100},
            "descriptive_statistics": {
                "ai_group": {"median": 22.0},
                "non_ai_group": {"median": 40.0}
            }
        }
        stats_file.write_text(json.dumps(stats_data))

        spot_check_results = {
            "false_negative_rate": 0.06,
            "misclassified_ai": 3,
            "total_sample_size": 50
        }

        # Create a dummy boxplot file
        boxplot_file = tmp_path / "boxplot.png"
        boxplot_file.write_bytes(b"dummy png content")

        output_file = tmp_path / "final_report.md"

        report = assemble_report(
            statistical_results_path=str(stats_file),
            spot_check_results=spot_check_results,
            boxplot_path=str(boxplot_file),
            output_path=str(output_file)
        )

        assert "![Boxplot]" in report
        assert "Figure 1:" in report

    def test_assemble_report_missing_statistical_results(self, tmp_path):
        """Test assembling report when statistical results file is missing."""
        with pytest.raises(FileNotFoundError, match="Statistical results file not found"):
            assemble_report(
                statistical_results_path=str(tmp_path / "nonexistent.json"),
                spot_check_results={"false_negative_rate": 0.05}
            )