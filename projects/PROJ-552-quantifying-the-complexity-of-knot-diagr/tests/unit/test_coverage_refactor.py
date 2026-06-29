"""
Unit tests for the refactored invariant coverage modules.

Tests coverage.py (pure calculations) and coverage_reporting.py (report generation).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from code.analysis.coverage import (
    InvariantCoverageEntry,
    InvariantCoverageReport,
    REQUIRED_INVARIANTS,
    _is_present,
    analyze_knot_invariant_coverage,
    calculate_coverage_statistics,
    load_cleaned_knots_data,
)
from code.analysis.coverage_reporting import (
    generate_invariant_coverage_report,
    save_coverage_entries_json,
    write_invariant_coverage_report_md,
)


class TestIsPresent:
    """Tests for the _is_present helper function."""

    def test_none_returns_false(self):
        assert _is_present(None) is False

    def test_empty_string_returns_false(self):
        assert _is_present("") is False
        assert _is_present("   ") is False

    def test_valid_values_return_true(self):
        assert _is_present("value") is True
        assert _is_present(0) is True
        assert _is_present(False) is True
        assert _is_present([]) is True  # Empty list is technically present


class TestAnalyzeKnotInvariantCoverage:
    """Tests for analyze_knot_invariant_coverage function."""

    def test_all_present(self):
        records = [
            {
                "knot_id": "test1",
                "crossing_number": "5",
                "braid_index": "3",
                "hyperbolic_volume": "1.23",
                "is_alternating": "True",
                "dt_code": "[1, 2, 3]",
                "braid_word": "1 2",
            }
        ]
        entries, missing_counts = analyze_knot_invariant_coverage(records)
        
        assert len(entries) == 1
        assert entries[0].total_present == 6
        assert entries[0].total_required == 6
        assert all(v == 0 for v in missing_counts.values())

    def test_all_missing(self):
        records = [
            {
                "knot_id": "test2",
                "crossing_number": "",
                "braid_index": None,
                "hyperbolic_volume": "",
                "is_alternating": None,
                "dt_code": "",
                "braid_word": None,
            }
        ]
        entries, missing_counts = analyze_knot_invariant_coverage(records)
        
        assert len(entries) == 1
        assert entries[0].total_present == 0
        assert entries[0].total_required == 6
        assert all(v == 1 for v in missing_counts.values())

    def test_partial_coverage(self):
        records = [
            {
                "knot_id": "test3",
                "crossing_number": "5",
                "braid_index": "",
                "hyperbolic_volume": "1.23",
                "is_alternating": "True",
                "dt_code": None,
                "braid_word": "1 2",
            }
        ]
        entries, missing_counts = analyze_knot_invariant_coverage(records)
        
        assert len(entries) == 1
        assert entries[0].total_present == 4
        assert entries[0].total_required == 6
        assert missing_counts["braid_index"] == 1
        assert missing_counts["dt_code"] == 1
        assert missing_counts["crossing_number"] == 0


class TestCalculateCoverageStatistics:
    """Tests for calculate_coverage_statistics function."""

    def test_single_knot_fully_covered(self):
        entries = [
            InvariantCoverageEntry(
                knot_id="k1",
                crossing_number_present=True,
                braid_index_present=True,
                hyperbolic_volume_present=True,
                is_alternating_present=True,
                dt_code_present=True,
                braid_word_present=True,
                total_present=6,
                total_required=6,
            )
        ]
        missing_counts = {inv: 0 for inv in REQUIRED_INVARIANTS}
        
        report = calculate_coverage_statistics(entries, missing_counts, 1)
        
        assert report.total_knots == 1
        assert report.fully_covered_count == 1
        assert report.partially_covered_count == 0
        assert report.fully_missing_count == 0
        assert all(v == 100.0 for v in report.coverage_per_invariant.values())

    def test_mixed_coverage(self):
        entries = [
            InvariantCoverageEntry(
                knot_id="k1",
                crossing_number_present=True,
                braid_index_present=True,
                hyperbolic_volume_present=True,
                is_alternating_present=True,
                dt_code_present=True,
                braid_word_present=True,
                total_present=6,
                total_required=6,
            ),
            InvariantCoverageEntry(
                knot_id="k2",
                crossing_number_present=True,
                braid_index_present=False,
                hyperbolic_volume_present=True,
                is_alternating_present=True,
                dt_code_present=False,
                braid_word_present=True,
                total_present=4,
                total_required=6,
            ),
            InvariantCoverageEntry(
                knot_id="k3",
                crossing_number_present=False,
                braid_index_present=False,
                hyperbolic_volume_present=False,
                is_alternating_present=False,
                dt_code_present=False,
                braid_word_present=False,
                total_present=0,
                total_required=6,
            ),
        ]
        missing_counts = {
            "crossing_number": 1,
            "braid_index": 2,
            "hyperbolic_volume": 1,
            "is_alternating": 1,
            "dt_code": 2,
            "braid_word": 1,
        }
        
        report = calculate_coverage_statistics(entries, missing_counts, 3)
        
        assert report.total_knots == 3
        assert report.fully_covered_count == 1
        assert report.partially_covered_count == 1
        assert report.fully_missing_count == 1
        
        # Check braid_index coverage: 1 present out of 3 = 33.33%
        assert abs(report.coverage_per_invariant["braid_index"] - 33.333333) < 0.01


class TestLoadCleanedKnotsData:
    """Tests for load_cleaned_knots_data function."""

    def test_load_from_csv(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            f.write("knot_id,crossing_number,braid_index\n")
            f.write("k1,5,3\n")
            f.write("k2,7,4\n")
            temp_path = Path(f.name)
        
        try:
            records = load_cleaned_knots_data(temp_path)
            assert len(records) == 2
            assert records[0]["knot_id"] == "k1"
            assert records[1]["knot_id"] == "k2"
        finally:
            temp_path.unlink()

    def test_missing_file_returns_empty(self):
        records = load_cleaned_knots_data(Path("/nonexistent/file.csv"))
        assert records == []


class TestSaveCoverageEntriesJson:
    """Tests for save_coverage_entries_json function."""

    def test_save_and_load(self):
        entries = [
            InvariantCoverageEntry(
                knot_id="k1",
                crossing_number_present=True,
                braid_index_present=True,
                hyperbolic_volume_present=True,
                is_alternating_present=True,
                dt_code_present=True,
                braid_word_present=True,
                total_present=6,
                total_required=6,
            )
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "entries.json"
            save_coverage_entries_json(entries, output_path)
            
            assert output_path.exists()
            with open(output_path, "r") as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]["knot_id"] == "k1"
            assert data[0]["total_present"] == 6


class TestWriteInvariantCoverageReportMd:
    """Tests for write_invariant_coverage_report_md function."""

    def test_generate_report(self):
        report = InvariantCoverageReport(
            total_knots=100,
            coverage_per_invariant={inv: 95.0 for inv in REQUIRED_INVARIANTS},
            missing_per_invariant={inv: 5 for inv in REQUIRED_INVARIANTS},
            fully_covered_count=90,
            partially_covered_count=5,
            fully_missing_count=5,
            entries=[],
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"
            write_invariant_coverage_report_md(report, output_path)
            
            assert output_path.exists()
            content = output_path.read_text()
            
            assert "Invariant Coverage Analysis" in content
            assert "Total knots analyzed: **100**" in content
            assert "90 knots" in content  # Fully covered
            assert "5 knots" in content  # Partially/Fully missing
            assert "95.00%" in content

    def test_report_creates_parent_dir(self):
        report = InvariantCoverageReport(
            total_knots=1,
            coverage_per_invariant={inv: 100.0 for inv in REQUIRED_INVARIANTS},
            missing_per_invariant={inv: 0 for inv in REQUIRED_INVARIANTS},
            fully_covered_count=1,
            partially_covered_count=0,
            fully_missing_count=0,
            entries=[],
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "report.md"
            write_invariant_coverage_report_md(report, output_path)
            
            assert output_path.exists()


class TestGenerateInvariantCoverageReport:
    """Tests for generate_invariant_coverage_report function."""

    def test_generate_detailed_report(self):
        entries = [
            InvariantCoverageEntry(
                knot_id="k1",
                crossing_number_present=True,
                braid_index_present=True,
                hyperbolic_volume_present=True,
                is_alternating_present=True,
                dt_code_present=True,
                braid_word_present=True,
                total_present=6,
                total_required=6,
            ),
            InvariantCoverageEntry(
                knot_id="k2",
                crossing_number_present=True,
                braid_index_present=False,
                hyperbolic_volume_present=True,
                is_alternating_present=True,
                dt_code_present=False,
                braid_word_present=True,
                total_present=4,
                total_required=6,
            ),
        ]
        missing_counts = {inv: 0 for inv in REQUIRED_INVARIANTS}
        missing_counts["braid_index"] = 1
        missing_counts["dt_code"] = 1
        
        report = calculate_coverage_statistics(entries, missing_counts, 2)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            output_path = generate_invariant_coverage_report(report, output_dir)
            
            assert output_path.exists()
            content = output_path.read_text()
            
            assert "Invariant Coverage Report" in content
            assert "Fully covered knots" in content
            assert "Partially covered knots" in content
            assert "| Invariant |" in content
            assert "k1" in content
            assert "k2" in content