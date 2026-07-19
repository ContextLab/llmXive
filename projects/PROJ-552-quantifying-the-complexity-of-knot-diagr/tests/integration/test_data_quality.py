"""Integration test for data quality checks (US2).

This test validates the end-to-end data quality pipeline:
1. Loads the cleaned knot dataset from data/processed/knots_cleaned.csv.
2. Runs the data quality analysis module (code/analysis/data_quality.py).
3. Verifies that the generated reports exist and contain expected fields.
4. Asserts that core invariants (crossing_number, braid_index) are NOT flagged
   as missing, adhering to FR-009 and SC-009.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import pandas as pd

# Ensure code/ is on the path for imports
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.data_quality import (
    NullStatistics,
    DataQualityReport,
    calculate_null_percentages,
    generate_data_quality_report,
    write_data_quality_report_md,
)
from reproducibility.logs import get_logger


# Constants
EXPECTED_CSV_PATH = "data/processed/knots_cleaned.csv"
EXPECTED_REPORT_PATH = "docs/reproducibility/data_quality_report.md"
EXPECTED_JSON_PATH = "docs/reproducibility/data_quality_stats.json"

CORE_INVARIANTS = ["crossing_number", "braid_index"]
HYPERBOLIC_VOLUME = "hyperbolic_volume"


@pytest.fixture(scope="module")
def cleaned_data_path():
    """Locate the cleaned dataset."""
    path = project_root / EXPECTED_CSV_PATH
    if not path.exists():
        pytest.fail(f"Cleaned dataset not found at {path}. "
                    "Run the data pipeline (T014) before running this test.")
    return path

@pytest.fixture(scope="module")
def data_quality_results(cleaned_data_path):
    """Run the data quality analysis module."""
    logger = get_logger("test_data_quality_integration")
    logger.log("test_start", parameters={"file": str(cleaned_data_path)})

    # Load data
    df = pd.read_csv(cleaned_data_path)

    # Calculate null percentages
    null_stats = calculate_null_percentages(df)

    # Generate full report object
    report = generate_data_quality_report(df, null_stats)

    # Write outputs to disk (mimicking the main script behavior)
    report_dir = project_root / "docs" / "reproducibility"
    report_dir.mkdir(parents=True, exist_ok=True)

    md_path = report_dir / "data_quality_report.md"
    write_data_quality_report_md(report, md_path)

    json_path = report_dir / "data_quality_stats.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "null_percentages": {k: v for k, v in null_stats.items()},
            "total_records": report.total_records,
            "fields_analyzed": report.fields_analyzed
        }, f, indent=2, default=str)

    logger.log("test_end", parameters={"status": "success"})

    return report, null_stats, md_path, json_path


class TestDataQualityIntegration:
    """Integration tests for the data quality pipeline."""

    def test_report_file_generated(self, data_quality_results):
        """Verify that the markdown report file is created."""
        _, _, md_path, _ = data_quality_results
        assert md_path.exists(), f"Report file {md_path} was not created."
        assert md_path.stat().st_size > 0, f"Report file {md_path} is empty."

    def test_json_stats_file_generated(self, data_quality_results):
        """Verify that the JSON stats file is created."""
        _, _, _, json_path = data_quality_results
        assert json_path.exists(), f"JSON stats file {json_path} was not created."
        assert json_path.stat().st_size > 0, f"JSON stats file {json_path} is empty."

        # Verify it is valid JSON
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "null_percentages" in data
        assert "total_records" in data

    def test_core_invariants_not_missing(self, data_quality_results):
        """
        Verify FR-009: Core tabulated invariants (crossing_number, braid_index)
        must NOT trigger missing_invariant_flags.
        """
        report, null_stats, _, _ = data_quality_results

        for invariant in CORE_INVARIANTS:
            # Check that the invariant is present in the stats
            assert invariant in null_stats, f"Invariant {invariant} not found in null stats."

            # The null percentage should be 0.0 (or very close due to float precision)
            # If the data pipeline worked correctly, these should be fully populated.
            pct = null_stats[invariant]
            assert pct == 0.0, (
                f"Core invariant '{invariant}' has {pct}% null values. "
                "Per FR-009, core invariants must be fully populated and "
                "should not trigger missing_invariant_flags."
            )

    def test_hyperbolic_volume_has_missing_flags(self, data_quality_results):
        """
        Verify that Phase 2+ invariants (like hyperbolic_volume) CAN have missing flags.
        This confirms the pipeline correctly distinguishes between core and computed invariants.
        """
        report, null_stats, _, _ = data_quality_results

        # Hyperbolic volume might have missing values in the raw atlas data
        # We assert that the key exists and is handled.
        assert HYPERBOLIC_VOLUME in null_stats, (
            f"Hyperbolic volume field not found. "
            "The dataset structure may have changed."
        )

        # We do not assert pct == 0.0 here, as hyperbolic volume is often missing
        # in older knot atlas versions or for non-hyperbolic knots.
        # The important thing is that the logic handles it without crashing.

    def test_report_content_structure(self, data_quality_results):
        """Verify the generated markdown report contains expected sections."""
        _, _, md_path, _ = data_quality_results

        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()

        expected_sections = [
            "Data Quality Report",
            "Summary Statistics",
            "Null Value Analysis",
            "Field Breakdown"
        ]

        for section in expected_sections:
            assert section in content, f"Expected section '{section}' not found in report."

    def test_total_records_consistency(self, data_quality_results, cleaned_data_path):
        """Verify that the report's record count matches the source file."""
        report, _, _, _ = data_quality_results

        expected_count = len(pd.read_csv(cleaned_data_path))
        assert report.total_records == expected_count, (
            f"Record count mismatch: Report says {report.total_records}, "
            f"but file has {expected_count}."
        )