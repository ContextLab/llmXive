"""
Unit tests for the inconsistency validator module (T025).

Tests:
1. Absolute p-difference > 0.05 threshold
2. Relative effect-size > 5% threshold
3. Inequality p-value handling (missing values)
4. Sample-size mismatch detection and data_quality_warning generation
5. Exclusion of sample-size mismatch entries from prevalence estimates
"""

import pytest
from pathlib import Path
import json
import tempfile
import os

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    check_p_value_consistency,
    check_effect_size_consistency,
    check_sample_size_consistency,
    validate_single_summary,
    validate_all_summaries,
    write_audit_report,
    get_excluded_records_for_prevalence,
    run_validator,
    ABSOLUTE_P_THRESHOLD,
    RELATIVE_EFFECT_SIZE_THRESHOLD,
    ERR_P_VALUE_MISMATCH,
    ERR_EFFECT_SIZE_MISMATCH,
    ERR_SAMPLE_SIZE_MISMATCH
)


class TestPValueConsistency:
    """Test absolute p-value difference threshold (FR-004)"""

    def test_p_value_within_threshold(self):
        """P-value difference <= 0.05 should be consistent"""
        is_consistent, diff = check_p_value_consistency(0.04, 0.043)
        assert is_consistent is True
        assert abs(diff - 0.003) < 1e-6

    def test_p_value_exceeds_threshold(self):
        """P-value difference > 0.05 should be inconsistent"""
        is_consistent, diff = check_p_value_consistency(0.01, 0.07)
        assert is_consistent is False
        assert abs(diff - 0.06) < 1e-6

    def test_p_value_missing_reported(self):
        """Missing reported p-value should return consistent"""
        is_consistent, diff = check_p_value_consistency(None, 0.05)
        assert is_consistent is True

    def test_p_value_missing_reconstructed(self):
        """Missing reconstructed p-value should return consistent"""
        is_consistent, diff = check_p_value_consistency(0.05, None)
        assert is_consistent is True


class TestEffectSizeConsistency:
    """Test relative effect-size difference threshold (FR-004)"""

    def test_effect_size_within_threshold(self):
        """Effect size difference <= 5% should be consistent"""
        is_consistent, diff = check_effect_size_consistency(0.10, 0.104)
        assert is_consistent is True
        assert abs(diff - 0.04) < 1e-6

    def test_effect_size_exceeds_threshold(self):
        """Effect size difference > 5% should be inconsistent"""
        is_consistent, diff = check_effect_size_consistency(0.10, 0.11)
        assert is_consistent is False
        assert abs(diff - 0.10) < 1e-6

    def test_effect_size_missing_reported(self):
        """Missing reported effect size should return consistent"""
        is_consistent, diff = check_effect_size_consistency(None, 0.05)
        assert is_consistent is True

    def test_effect_size_missing_reconstructed(self):
        """Missing reconstructed effect size should return consistent"""
        is_consistent, diff = check_effect_size_consistency(0.05, None)
        assert is_consistent is True

    def test_effect_size_zero_reported(self):
        """Zero reported effect size with non-zero reconstructed should be inconsistent"""
        is_consistent, diff = check_effect_size_consistency(0.0, 0.01)
        assert is_consistent is False
        assert diff == 1.0


class TestSampleSizeConsistency:
    """Test sample size mismatch detection (FR-004b)"""

    def test_sample_sizes_match(self):
        """Matching sample sizes should be consistent"""
        is_consistent, msg = check_sample_size_consistency(
            100, 100, 100, 100
        )
        assert is_consistent is True
        assert msg == ""

    def test_sample_size_control_mismatch(self):
        """Control sample size mismatch should be inconsistent"""
        is_consistent, msg = check_sample_size_consistency(
            100, 100, 105, 100
        )
        assert is_consistent is False
        assert "Sample size mismatch" in msg
        assert "n_control=100" in msg

    def test_sample_size_treatment_mismatch(self):
        """Treatment sample size mismatch should be inconsistent"""
        is_consistent, msg = check_sample_size_consistency(
            100, 100, 100, 95
        )
        assert is_consistent is False
        assert "Sample size mismatch" in msg
        assert "n_treatment=100" in msg

    def test_sample_size_both_mismatch(self):
        """Both sample sizes mismatch should be inconsistent"""
        is_consistent, msg = check_sample_size_consistency(
            100, 100, 105, 95
        )
        assert is_consistent is False
        assert "Sample size mismatch" in msg

    def test_sample_size_missing_values(self):
        """Missing values should be consistent (cannot verify)"""
        is_consistent, msg = check_sample_size_consistency(
            None, 100, 100, 100
        )
        assert is_consistent is True
        assert msg == ""


class TestValidateSingleSummary:
    """Test full validation of a single summary"""

    def test_all_consistent(self):
        """All checks pass -> is_consistent=True, no warnings"""
        summary = ABTestSummary(
            source_url="http://example.com/test1",
            domain="tech",
            reported_p_value=0.04,
            reported_effect_size=0.10,
            n_control=100,
            n_treatment=100,
            baseline_rate=0.5,
            variant_rate=0.6
        )
        reconstructed = {
            'p_value': 0.042,
            'effect_size': 0.102,
            'n_control': 100,
            'n_treatment': 100,
            'test_type': 'z-test'
        }

        record = validate_single_summary(summary, reconstructed)

        assert record.is_consistent is True
        assert len(record.inconsistencies) == 0
        assert record.data_quality_warnings is None

    def test_p_value_inconsistent(self):
        """P-value inconsistency -> is_consistent=False"""
        summary = ABTestSummary(
            source_url="http://example.com/test2",
            domain="tech",
            reported_p_value=0.01,
            reported_effect_size=0.10,
            n_control=100,
            n_treatment=100,
            baseline_rate=0.5,
            variant_rate=0.6
        )
        reconstructed = {
            'p_value': 0.08,
            'effect_size': 0.10,
            'n_control': 100,
            'n_treatment': 100,
            'test_type': 'z-test'
        }

        record = validate_single_summary(summary, reconstructed)

        assert record.is_consistent is False
        assert len(record.inconsistencies) == 1
        assert record.inconsistencies[0]['type'] == 'p_value_mismatch'
        assert record.inconsistencies[0]['code'] == ERR_P_VALUE_MISMATCH

    def test_effect_size_inconsistent(self):
        """Effect size inconsistency -> is_consistent=False"""
        summary = ABTestSummary(
            source_url="http://example.com/test3",
            domain="tech",
            reported_p_value=0.04,
            reported_effect_size=0.10,
            n_control=100,
            n_treatment=100,
            baseline_rate=0.5,
            variant_rate=0.6
        )
        reconstructed = {
            'p_value': 0.04,
            'effect_size': 0.15,
            'n_control': 100,
            'n_treatment': 100,
            'test_type': 'z-test'
        }

        record = validate_single_summary(summary, reconstructed)

        assert record.is_consistent is False
        assert len(record.inconsistencies) == 1
        assert record.inconsistencies[0]['type'] == 'effect_size_mismatch'
        assert record.inconsistencies[0]['code'] == ERR_EFFECT_SIZE_MISMATCH

    def test_sample_size_mismatch_warning(self):
        """Sample size mismatch -> data_quality_warning generated"""
        summary = ABTestSummary(
            source_url="http://example.com/test4",
            domain="tech",
            reported_p_value=0.04,
            reported_effect_size=0.10,
            n_control=100,
            n_treatment=100,
            baseline_rate=0.5,
            variant_rate=0.6
        )
        reconstructed = {
            'p_value': 0.04,
            'effect_size': 0.10,
            'n_control': 105,
            'n_treatment': 100,
            'test_type': 'z-test'
        }

        record = validate_single_summary(summary, reconstructed)

        assert record.is_consistent is True  # Only warning, not inconsistency
        assert len(record.inconsistencies) == 1
        assert record.inconsistencies[0]['type'] == 'sample_size_mismatch'
        assert record.inconsistencies[0]['code'] == ERR_SAMPLE_SIZE_MISMATCH
        assert record.data_quality_warnings is not None
        assert len(record.data_quality_warnings) == 1
        assert "Sample size mismatch" in record.data_quality_warnings[0]

    def test_multiple_issues(self):
        """Multiple issues -> all recorded"""
        summary = ABTestSummary(
            source_url="http://example.com/test5",
            domain="tech",
            reported_p_value=0.01,
            reported_effect_size=0.10,
            n_control=100,
            n_treatment=100,
            baseline_rate=0.5,
            variant_rate=0.6
        )
        reconstructed = {
            'p_value': 0.08,
            'effect_size': 0.15,
            'n_control': 105,
            'n_treatment': 100,
            'test_type': 'z-test'
        }

        record = validate_single_summary(summary, reconstructed)

        assert record.is_consistent is False
        assert len(record.inconsistencies) == 3  # p, effect, sample
        assert record.data_quality_warnings is not None


class TestExclusionFromPrevalence:
    """Test FR-004b: exclusion of sample-size mismatch entries"""

    def test_exclude_sample_mismatch_records(self):
        """Records with sample_size_mismatch should be excluded"""
        records = [
            AuditRecord(
                source_url="url1",
                domain="tech",
                test_type="z-test",
                is_consistent=True,
                inconsistencies=[
                    {
                        "type": "sample_size_mismatch",
                        "code": ERR_SAMPLE_SIZE_MISMATCH,
                        "message": "Sample size mismatch"
                    }
                ],
                data_quality_warnings=["Sample size mismatch"],
                validated_at="2024-01-01T00:00:00Z"
            ),
            AuditRecord(
                source_url="url2",
                domain="tech",
                test_type="z-test",
                is_consistent=True,
                inconsistencies=[],
                data_quality_warnings=None,
                validated_at="2024-01-01T00:00:00Z"
            ),
            AuditRecord(
                source_url="url3",
                domain="tech",
                test_type="z-test",
                is_consistent=False,
                inconsistencies=[
                    {
                        "type": "p_value_mismatch",
                        "code": ERR_P_VALUE_MISMATCH,
                        "message": "P-value mismatch"
                    }
                ],
                data_quality_warnings=None,
                validated_at="2024-01-01T00:00:00Z"
            )
        ]

        excluded = get_excluded_records_for_prevalence(records)

        # Should exclude only the sample_size_mismatch record
        assert len(excluded) == 2
        assert excluded[0].source_url == "url2"
        assert excluded[1].source_url == "url3"
        assert all(
            not any(inc['type'] == 'sample_size_mismatch' for inc in r.inconsistencies)
            for r in excluded
        )


class TestWriteAuditReport:
    """Test writing audit report to JSON"""

    def test_write_report(self):
        """Report should be written to file with correct structure"""
        records = [
            AuditRecord(
                source_url="http://example.com/test1",
                domain="tech",
                test_type="z-test",
                is_consistent=False,
                inconsistencies=[
                    {
                        "type": "p_value_mismatch",
                        "code": ERR_P_VALUE_MISMATCH,
                        "message": "P-value mismatch"
                    }
                ],
                data_quality_warnings=None,
                validated_at="2024-01-01T00:00:00Z"
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "audit_report.json"
            write_audit_report(records, output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert len(data) == 1
            assert data[0]['source_url'] == "http://example.com/test1"
            assert data[0]['is_consistent'] is False
            assert 'inconsistencies' in data[0]
            assert 'data_quality_warnings' in data[0]


class TestRunValidator:
    """Test the main run_validator function"""

    def test_run_validator_full_flow(self):
        """Full validation flow from files to output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create summaries file
            summaries_data = [
                {
                    "source_url": "http://example.com/test1",
                    "domain": "tech",
                    "reported_p_value": 0.01,
                    "reported_effect_size": 0.10,
                    "n_control": 100,
                    "n_treatment": 100,
                    "baseline_rate": 0.5,
                    "variant_rate": 0.6
                }
            ]
            summaries_path = tmpdir_path / "summaries.json"
            with open(summaries_path, 'w') as f:
                json.dump(summaries_data, f)

            # Create reconstructed stats file
            reconstructed_data = [
                {
                    "p_value": 0.08,
                    "effect_size": 0.10,
                    "n_control": 100,
                    "n_treatment": 100,
                    "test_type": "z-test"
                }
            ]
            reconstructed_path = tmpdir_path / "reconstructed.json"
            with open(reconstructed_path, 'w') as f:
                json.dump(reconstructed_data, f)

            # Run validator
            output_path = tmpdir_path / "audit_report.json"
            records = run_validator(summaries_path, reconstructed_path, output_path)

            # Verify results
            assert len(records) == 1
            assert records[0].is_consistent is False
            assert output_path.exists()