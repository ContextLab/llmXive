"""
Unit tests for data quality analysis module.

Tests for T028: Compute null percentage for required invariant fields
and document in docs/reproducibility/data_quality_report.md
"""

import pytest
from pathlib import Path
import pandas as pd
from io import StringIO

from analysis.data_quality import (
    calculate_null_percentages,
    generate_data_quality_report,
    write_data_quality_report_md,
    NullStatistics,
    DataQualityReport
)


class TestCalculateNullPercentages:
    """Tests for calculate_null_percentages function."""

    def test_no_nulls(self):
        """Test when no null values exist."""
        df = pd.DataFrame({
            "crossing_number": [1, 2, 3, 4, 5],
            "braid_index": [1, 2, 2, 3, 3],
            "hyperbolic_volume": [0.5, 1.0, 1.5, 2.0, 2.5],
            "is_alternating": [True, False, True, True, False]
        })
        required_fields = ["crossing_number", "braid_index", "hyperbolic_volume", "is_alternating"]

        stats = calculate_null_percentages(df, required_fields)

        assert len(stats) == 4
        for stat in stats:
            assert stat.null_count == 0
            assert stat.null_percentage == 0.0

    def test_with_nulls(self):
        """Test when null values exist in some fields."""
        df = pd.DataFrame({
            "crossing_number": [1, 2, None, 4, 5],
            "braid_index": [1, None, 2, 3, 3],
            "hyperbolic_volume": [0.5, 1.0, 1.5, None, 2.5],
            "is_alternating": [True, False, True, True, False]
        })
        required_fields = ["crossing_number", "braid_index", "hyperbolic_volume", "is_alternating"]

        stats = calculate_null_percentages(df, required_fields)

        assert len(stats) == 4
        # crossing_number: 1/5 = 20%
        crossing_stat = next(s for s in stats if s.field_name == "crossing_number")
        assert crossing_stat.null_count == 1
        assert crossing_stat.null_percentage == 20.0

        # braid_index: 1/5 = 20%
        braid_stat = next(s for s in stats if s.field_name == "braid_index")
        assert braid_stat.null_count == 1
        assert braid_stat.null_percentage == 20.0

        # hyperbolic_volume: 1/5 = 20%
        volume_stat = next(s for s in stats if s.field_name == "hyperbolic_volume")
        assert volume_stat.null_count == 1
        assert volume_stat.null_percentage == 20.0

        # is_alternating: 0/5 = 0%
        alt_stat = next(s for s in stats if s.field_name == "is_alternating")
        assert alt_stat.null_count == 0
        assert alt_stat.null_percentage == 0.0

    def test_empty_dataframe(self):
        """Test when dataframe is empty."""
        df = pd.DataFrame(columns=["crossing_number", "braid_index"])
        required_fields = ["crossing_number", "braid_index"]

        stats = calculate_null_percentages(df, required_fields)

        assert len(stats) == 2
        for stat in stats:
            assert stat.total_records == 0
            assert stat.null_count == 0
            assert stat.null_percentage == 0.0

    def test_missing_field(self):
        """Test when a required field is not in dataframe."""
        df = pd.DataFrame({
            "crossing_number": [1, 2, 3],
            "braid_index": [1, 2, 2]
        })
        required_fields = ["crossing_number", "braid_index", "hyperbolic_volume"]

        stats = calculate_null_percentages(df, required_fields)

        assert len(stats) == 3
        # hyperbolic_volume is missing, so 100% null
        vol_stat = next(s for s in stats if s.field_name == "hyperbolic_volume")
        assert vol_stat.null_count == 3
        assert vol_stat.null_percentage == 100.0


class TestGenerateDataQualityReport:
    """Tests for generate_data_quality_report function."""

    def test_report_structure(self):
        """Test that report has correct structure."""
        df = pd.DataFrame({
            "crossing_number": [1, 2, 3, 4, 5],
            "braid_index": [1, 2, 2, 3, 3],
            "hyperbolic_volume": [0.5, 1.0, 1.5, 2.0, 2.5],
            "is_alternating": [True, False, True, True, False]
        })
        required_fields = ["crossing_number", "braid_index", "hyperbolic_volume", "is_alternating"]

        report = generate_data_quality_report(df, required_fields)

        assert isinstance(report, DataQualityReport)
        assert report.total_records == 5
        assert len(report.null_statistics) == 4
        assert report.passes_threshold is True
        assert report.threshold_percentage == 5.0

    def test_threshold_failure(self):
        """Test when null percentage exceeds threshold."""
        df = pd.DataFrame({
            "crossing_number": [1, 2, None, None, None],  # 60% null
            "braid_index": [1, 2, 2, 3, 3],
            "hyperbolic_volume": [0.5, 1.0, 1.5, 2.0, 2.5],
            "is_alternating": [True, False, True, True, False]
        })
        required_fields = ["crossing_number", "braid_index", "hyperbolic_volume", "is_alternating"]

        report = generate_data_quality_report(df, required_fields, threshold_percentage=5.0)

        assert report.passes_threshold is False
        crossing_stat = next(s for s in report.null_statistics if s.field_name == "crossing_number")
        assert crossing_stat.null_percentage == 60.0

    def test_custom_threshold(self):
        """Test with custom threshold value."""
        df = pd.DataFrame({
            "crossing_number": [1, 2, None, 4, 5],  # 20% null
            "braid_index": [1, 2, 2, 3, 3],
            "hyperbolic_volume": [0.5, 1.0, 1.5, 2.0, 2.5],
            "is_alternating": [True, False, True, True, False]
        })
        required_fields = ["crossing_number", "braid_index", "hyperbolic_volume", "is_alternating"]

        # With 25% threshold, should pass
        report = generate_data_quality_report(df, required_fields, threshold_percentage=25.0)
        assert report.passes_threshold is True
        assert report.threshold_percentage == 25.0


class TestWriteDataQualityReportMd:
    """Tests for write_data_quality_report_md function."""

    def test_report_file_created(self, tmp_path):
        """Test that report file is created."""
        report = DataQualityReport(
            total_records=100,
            required_fields=["crossing_number", "braid_index"],
            null_statistics=[
                NullStatistics("crossing_number", 100, 0, 0.0),
                NullStatistics("braid_index", 100, 5, 5.0)
            ],
            overall_null_percentage=2.5,
            generated_at="2024-01-01T00:00:00",
            passes_threshold=True
        )

        output_path = tmp_path / "data_quality_report.md"
        write_data_quality_report_md(report, output_path)

        assert output_path.exists()

    def test_report_content(self, tmp_path):
        """Test that report contains expected content."""
        report = DataQualityReport(
            total_records=100,
            required_fields=["crossing_number", "braid_index"],
            null_statistics=[
                NullStatistics("crossing_number", 100, 0, 0.0),
                NullStatistics("braid_index", 100, 5, 5.0)
            ],
            overall_null_percentage=2.5,
            generated_at="2024-01-01T00:00:00",
            passes_threshold=True
        )

        output_path = tmp_path / "data_quality_report.md"
        write_data_quality_report_md(report, output_path)

        content = output_path.read_text()

        # Check for required sections
        assert "# Data Quality Report" in content
        assert "Total records analyzed" in content
        assert "Required Invariant Fields" in content
        assert "crossing_number" in content
        assert "braid_index" in content
        assert "PASS" in content
        assert "FR-002" in content
        assert "SC-013" in content

    def test_report_with_failing_threshold(self, tmp_path):
        """Test report when threshold is not met."""
        report = DataQualityReport(
            total_records=100,
            required_fields=["crossing_number"],
            null_statistics=[
                NullStatistics("crossing_number", 100, 10, 10.0)
            ],
            overall_null_percentage=10.0,
            generated_at="2024-01-01T00:00:00",
            passes_threshold=False
        )

        output_path = tmp_path / "data_quality_report.md"
        write_data_quality_report_md(report, output_path)

        content = output_path.read_text()

        assert "FAIL" in content
        assert "exceed the FR-002 threshold" in content
