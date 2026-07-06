"""
Unit tests for the Inconsistency Validator (T025).

Tests:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Sample-size mismatch detection and exclusion from prevalence
- AuditRecord generation with data_quality_warning
"""
import pytest
from pathlib import Path
import json
import sys
from datetime import datetime

# Add code to path if not already
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    calculate_absolute_p_difference,
    calculate_relative_effect_size_difference,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency,
    create_audit_record,
    validate_summary,
    validate_all_summaries,
    filter_for_prevalence,
    write_audit_report
)


class TestAbsolutePDifference:
    def test_within_threshold(self):
        diff = calculate_absolute_p_difference(0.04, 0.08)
        assert diff == 0.04
        assert diff <= 0.05

    def test_exceeds_threshold(self):
        diff = calculate_absolute_p_difference(0.01, 0.07)
        assert diff == 0.06
        assert diff > 0.05

    def test_exact_threshold(self):
        diff = calculate_absolute_p_difference(0.05, 0.10)
        assert diff == 0.05
        # Threshold is > 0.05, so 0.05 is consistent
        assert not (diff > 0.05)


class TestRelativeEffectSizeDifference:
    def test_within_threshold(self):
        diff = calculate_relative_effect_size_difference(0.10, 0.11)
        # |0.10 - 0.11| / 0.11 = 0.01 / 0.11 = 0.0909... ~ 9% -> Wait, 0.10 vs 0.11 is 10% diff?
        # 0.11 - 0.10 = 0.01. 0.01 / 0.11 = 0.0909. That is > 5%.
        # Let's use closer numbers. 0.10 vs 0.104 -> 0.004/0.104 = 0.038 < 0.05
        diff = calculate_relative_effect_size_difference(0.10, 0.104)
        assert diff < 0.05

    def test_exceeds_threshold(self):
        # 0.10 vs 0.11 -> 9% diff > 5%
        diff = calculate_relative_effect_size_difference(0.10, 0.11)
        assert diff > 0.05

    def test_zero_reported_nonzero_reconstructed(self):
        diff = calculate_relative_effect_size_difference(0.05, 0.0)
        assert diff == float('inf')

    def test_both_zero(self):
        diff = calculate_relative_effect_size_difference(0.0, 0.0)
        assert diff == 0.0


class TestSampleSizeMismatch:
    def test_missing_n_control(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            year=2023,
            n_control=None,
            n_treatment=100,
            p_value=0.03,
            effect_size=0.1
        )
        assert detect_sample_size_mismatch(summary) is True

    def test_missing_n_treatment(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            year=2023,
            n_control=100,
            n_treatment=None,
            p_value=0.03,
            effect_size=0.1
        )
        assert detect_sample_size_mismatch(summary) is True

    def test_zero_n_control(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            year=2023,
            n_control=0,
            n_treatment=100,
            p_value=0.03,
            effect_size=0.1
        )
        assert detect_sample_size_mismatch(summary) is True

    def test_valid_sample_sizes(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            year=2023,
            n_control=100,
            n_treatment=100,
            p_value=0.03,
            effect_size=0.1
        )
        assert detect_sample_size_mismatch(summary) is False


class TestValidateSummary:
    def test_all_consistent(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            year=2023,
            n_control=100,
            n_treatment=100,
            p_value=0.05,
            effect_size=0.10
        )
        record = validate_summary(summary, 0.051, 0.102)
        assert record.is_inconsistent is False
        assert record.data_quality_warnings is None

    def test_p_inconsistent(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            year=2023,
            n_control=100,
            n_treatment=100,
            p_value=0.01,
            effect_size=0.10
        )
        record = validate_summary(summary, 0.08, 0.102) # Diff 0.07 > 0.05
        assert record.is_inconsistent is True
        assert any("P-value inconsistency" in note for note in record.notes)

    def test_effect_inconsistent(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            year=2023,
            n_control=100,
            n_treatment=100,
            p_value=0.05,
            effect_size=0.10
        )
        record = validate_summary(summary, 0.051, 0.15) # Diff ~50% > 5%
        assert record.is_inconsistent is True
        assert any("Effect size inconsistency" in note for note in record.notes)

    def test_sample_size_mismatch_flagged(self):
        summary = ABTestSummary(
            source_url="http://example.com",
            domain="tech",
            year=2023,
            n_control=None,
            n_treatment=100,
            p_value=0.05,
            effect_size=0.10
        )
        record = validate_summary(summary, 0.051, 0.102)
        assert record.is_inconsistent is True
        assert record.data_quality_warnings is not None
        assert any("Sample size mismatch" in w for w in record.data_quality_warnings)


class TestFilterForPrevalence:
    def test_excludes_mismatch(self):
        records = [
            AuditRecord(
                source_url="http://ok.com",
                domain="tech",
                year=2023,
                is_inconsistent=False,
                p_value_reported=0.05,
                p_value_reconstructed=0.05,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.1,
                notes=[],
                data_quality_warnings=None
            ),
            AuditRecord(
                source_url="http://bad.com",
                domain="tech",
                year=2023,
                is_inconsistent=True,
                p_value_reported=0.05,
                p_value_reconstructed=0.05,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.1,
                notes=["Sample size mismatch"],
                data_quality_warnings=["Sample size mismatch detected"]
            )
        ]
        filtered = filter_for_prevalence(records)
        assert len(filtered) == 1
        assert filtered[0].source_url == "http://ok.com"

    def test_all_valid(self):
        records = [
            AuditRecord(
                source_url="http://ok1.com",
                domain="tech",
                year=2023,
                is_inconsistent=False,
                p_value_reported=0.05,
                p_value_reconstructed=0.05,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.1,
                notes=[],
                data_quality_warnings=None
            ),
            AuditRecord(
                source_url="http://ok2.com",
                domain="tech",
                year=2023,
                is_inconsistent=True, # Inconsistent stats but valid sample size
                p_value_reported=0.01,
                p_value_reconstructed=0.08,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.1,
                notes=["P-value inconsistency"],
                data_quality_warnings=None
            )
        ]
        filtered = filter_for_prevalence(records)
        # Both should be included because neither has sample size mismatch warning
        assert len(filtered) == 2


class TestWriteAuditReport:
    def test_writes_json(self, tmp_path):
        records = [
            AuditRecord(
                source_url="http://test.com",
                domain="tech",
                year=2023,
                is_inconsistent=False,
                p_value_reported=0.05,
                p_value_reconstructed=0.05,
                effect_size_reported=0.1,
                effect_size_reconstructed=0.1,
                notes=[],
                data_quality_warnings=None
            )
        ]
        output_file = tmp_path / "audit_report.json"
        write_audit_report(records, output_file)
        
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["source_url"] == "http://test.com"