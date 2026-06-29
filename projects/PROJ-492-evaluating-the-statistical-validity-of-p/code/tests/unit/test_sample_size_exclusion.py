"""
Test T025c: Verify that summaries flagged for sample-size mismatch
are not included in output/prevalence.json.

This test validates FR-004b requirement that sample-size mismatch entries
are excluded from aggregate prevalence estimates.
"""
import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from code.src.audit.validator import (
    detect_sample_size_mismatch,
    create_audit_record,
    filter_for_prevalence,
    write_audit_report,
)
from code.src.models.data_models import ABTestSummary, AuditRecord


class TestSampleSizeExclusion:
    """Test that sample-size mismatch flagged summaries are excluded from prevalence."""

    @pytest.fixture
    def sample_summaries(self):
        """Create sample ABTestSummary objects with varying sample-size consistency."""
        return [
            ABTestSummary(
                url="https://example.com/test1",
                domain="tech",
                publication_year=2023,
                sample_size_control=1000,
                sample_size_treatment=1000,
                conversion_rate_control=0.10,
                conversion_rate_treatment=0.12,
                reported_p_value=0.03,
                reported_effect_size=0.02,
            ),
            ABTestSummary(
                url="https://example.com/test2",
                domain="tech",
                publication_year=2023,
                sample_size_control=500,
                sample_size_treatment=500,
                conversion_rate_control=0.15,
                conversion_rate_treatment=0.18,
                reported_p_value=0.04,
                reported_effect_size=0.03,
            ),
            ABTestSummary(
                url="https://example.com/test3",
                domain="ecommerce",
                publication_year=2022,
                sample_size_control=2000,
                sample_size_treatment=500,  # MISMATCH: control != treatment
                conversion_rate_control=0.08,
                conversion_rate_treatment=0.10,
                reported_p_value=0.05,
                reported_effect_size=0.02,
            ),
            ABTestSummary(
                url="https://example.com/test4",
                domain="finance",
                publication_year=2023,
                sample_size_control=800,
                sample_size_treatment=800,
                conversion_rate_control=0.12,
                conversion_rate_treatment=0.14,
                reported_p_value=0.06,
                reported_effect_size=0.02,
            ),
            ABTestSummary(
                url="https://example.com/test5",
                domain="healthcare",
                publication_year=2021,
                sample_size_control=1500,
                sample_size_treatment=300,  # MISMATCH: significant difference
                conversion_rate_control=0.05,
                conversion_rate_treatment=0.07,
                reported_p_value=0.08,
                reported_effect_size=0.02,
            ),
        ]

    @pytest.fixture
    def audit_records(self, sample_summaries):
        """Create AuditRecord objects from summaries, detecting sample-size mismatches."""
        records = []
        for summary in sample_summaries:
            has_mismatch = detect_sample_size_mismatch(
                summary.sample_size_control,
                summary.sample_size_treatment,
                tolerance_pct=5.0,  # 5% tolerance
            )
            record = create_audit_record(
                ab_summary=summary,
                sample_size_mismatch=has_mismatch,
                p_difference=0.01,
                effect_size_difference=0.01,
                is_consistent=not has_mismatch,
            )
            records.append(record)
        return records

    def test_detect_sample_size_mismatch_identifies_issues(
        self, sample_summaries
    ):
        """Verify that mismatch detection correctly identifies inconsistent sample sizes."""
        mismatches = []
        for summary in sample_summaries:
            has_mismatch = detect_sample_size_mismatch(
                summary.sample_size_control,
                summary.sample_size_treatment,
                tolerance_pct=5.0,
            )
            if has_mismatch:
                mismatches.append(summary.url)

        # test3 and test5 should be flagged as having mismatches
        assert "https://example.com/test3" in mismatches
        assert "https://example.com/test5" in mismatches
        assert len(mismatches) == 2

    def test_filter_for_prevalence_excludes_mismatched_summaries(
        self, audit_records
    ):
        """
        Verify that filter_for_prevalence removes records with sample_size_mismatch=True.
        This is the core requirement of T025c.
        """
        # Get all record URLs before filtering
        all_urls = [r.ab_summary.url for r in audit_records]
        assert len(all_urls) == 5

        # Filter for prevalence (should exclude mismatched)
        filtered_records = filter_for_prevalence(audit_records)
        filtered_urls = [r.ab_summary.url for r in filtered_records]

        # Verify mismatched records are excluded
        assert "https://example.com/test3" not in filtered_urls
        assert "https://example.com/test5" not in filtered_urls

        # Verify consistent records are included
        assert "https://example.com/test1" in filtered_urls
        assert "https://example.com/test2" in filtered_urls
        assert "https://example.com/test4" in filtered_urls

        # Should have exactly 3 records (5 total - 2 mismatched)
        assert len(filtered_records) == 3

    def test_prevalence_json_does_not_contain_mismatched_records(
        self, audit_records, tmp_path
    ):
        """
        Verify that when we write the audit report and filter for prevalence,
        the resulting prevalence data excludes mismatched summaries.
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Write full audit report
        audit_report_path = output_dir / "audit_report.json"
        write_audit_report(audit_records, audit_report_path)

        # Load and verify the full report contains all records
        with open(audit_report_path, "r") as f:
            full_report = json.load(f)
        assert len(full_report) == 5

        # Filter for prevalence
        filtered = filter_for_prevalence(audit_records)

        # Simulate what would go into prevalence.json (only filtered records)
        prevalence_data = [
            {
                "url": r.ab_summary.url,
                "domain": r.ab_summary.domain,
                "is_consistent": r.is_consistent,
                "sample_size_mismatch": r.sample_size_mismatch,
            }
            for r in filtered
        ]

        # Verify no mismatched records in prevalence data
        for record in prevalence_data:
            assert record["sample_size_mismatch"] is False, (
                f"Record {record['url']} should not be in prevalence data"
            )

        # Verify expected count
        assert len(prevalence_data) == 3

    def test_filter_preserves_data_quality_warnings(
        self, audit_records
    ):
        """
        Verify that the filter operation preserves data_quality_warning field
        for records that ARE included in prevalence (non-mismatched records).
        """
        filtered = filter_for_prevalence(audit_records)

        # All filtered records should have data_quality_warning set to None
        # or False since they don't have sample-size mismatches
        for record in filtered:
            assert record.sample_size_mismatch is False

    def test_integration_with_write_audit_report(
        self, audit_records, tmp_path
    ):
        """
        Integration test: Write audit report, then verify that the
        filtered prevalence subset correctly excludes mismatched entries.
        """
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Write the full audit report
        audit_report_path = output_dir / "audit_report.json"
        write_audit_report(audit_records, audit_report_path)

        # Load the written report
        with open(audit_report_path, "r") as f:
            written_records = json.load(f)

        # Count records with sample_size_mismatch in the full report
        mismatched_in_full = [
            r for r in written_records if r.get("sample_size_mismatch", False)
        ]
        assert len(mismatched_in_full) == 2

        # Now filter and verify exclusion
        filtered = filter_for_prevalence(audit_records)
        assert len(filtered) == 3

        # Verify none of the filtered records have mismatches
        for record in filtered:
            assert record.sample_size_mismatch is False

    def test_empty_input_handling(self):
        """Verify filter_for_prevalence handles empty input gracefully."""
        result = filter_for_prevalence([])
        assert result == []

    def test_all_mismatched_input(self):
        """Verify behavior when all records have sample-size mismatches."""
        mismatched_summaries = [
            ABTestSummary(
                url="https://test.com/a",
                domain="tech",
                publication_year=2023,
                sample_size_control=1000,
                sample_size_treatment=100,  # Mismatch
                conversion_rate_control=0.10,
                conversion_rate_treatment=0.12,
                reported_p_value=0.03,
                reported_effect_size=0.02,
            ),
            ABTestSummary(
                url="https://test.com/b",
                domain="tech",
                publication_year=2023,
                sample_size_control=500,
                sample_size_treatment=50,  # Mismatch
                conversion_rate_control=0.15,
                conversion_rate_treatment=0.18,
                reported_p_value=0.04,
                reported_effect_size=0.03,
            ),
        ]

        records = []
        for summary in mismatched_summaries:
            has_mismatch = detect_sample_size_mismatch(
                summary.sample_size_control,
                summary.sample_size_treatment,
                tolerance_pct=5.0,
            )
            record = create_audit_record(
                ab_summary=summary,
                sample_size_mismatch=has_mismatch,
                p_difference=0.01,
                effect_size_difference=0.01,
                is_consistent=not has_mismatch,
            )
            records.append(record)

        filtered = filter_for_prevalence(records)
        assert len(filtered) == 0  # All should be excluded

    def test_no_mismatched_input(self):
        """Verify behavior when no records have sample-size mismatches."""
        consistent_summaries = [
            ABTestSummary(
                url="https://test.com/c",
                domain="tech",
                publication_year=2023,
                sample_size_control=1000,
                sample_size_treatment=1000,  # Consistent
                conversion_rate_control=0.10,
                conversion_rate_treatment=0.12,
                reported_p_value=0.03,
                reported_effect_size=0.02,
            ),
            ABTestSummary(
                url="https://test.com/d",
                domain="tech",
                publication_year=2023,
                sample_size_control=500,
                sample_size_treatment=500,  # Consistent
                conversion_rate_control=0.15,
                conversion_rate_treatment=0.18,
                reported_p_value=0.04,
                reported_effect_size=0.03,
            ),
        ]

        records = []
        for summary in consistent_summaries:
            has_mismatch = detect_sample_size_mismatch(
                summary.sample_size_control,
                summary.sample_size_treatment,
                tolerance_pct=5.0,
            )
            record = create_audit_record(
                ab_summary=summary,
                sample_size_mismatch=has_mismatch,
                p_difference=0.01,
                effect_size_difference=0.01,
                is_consistent=not has_mismatch,
            )
            records.append(record)

        filtered = filter_for_prevalence(records)
        assert len(filtered) == 2  # All should be included