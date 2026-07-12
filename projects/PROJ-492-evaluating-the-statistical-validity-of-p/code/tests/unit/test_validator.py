"""
Unit tests for the Inconsistency Validator (T025).
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    run_validator,
    calculate_relative_effect_size_diff,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD
)


class TestCalculateRelativeEffectSizeDiff:
    def test_normal_case(self):
        reported = 0.10
        reconstructed = 0.11
        # |0.10 - 0.11| / 0.10 = 0.1
        expected = 0.1
        assert abs(calculate_relative_effect_size_diff(reported, reconstructed) - expected) < 1e-9

    def test_zero_reported(self):
        assert calculate_relative_effect_size_diff(0.0, 0.1) is None

    def test_none_values(self):
        assert calculate_relative_effect_size_diff(None, 0.1) is None
        assert calculate_relative_effect_size_diff(0.1, None) is None


class TestValidateSingleSummary:
    def test_consistent_case(self):
        summary = ABTestSummary(
            id="test-1",
            url="http://example.com/1",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.03,
            effect_size=0.05
        )
        reconstructed = {
            "n_control": 1000,
            "n_treatment": 1000,
            "p_value": 0.031,
            "effect_size": 0.051
        }

        record = validate_single_summary(summary, reconstructed)

        assert record.is_inconsistent is False
        assert record.is_excluded_from_prevalence is False
        assert len(record.issues) == 0
        assert record.sample_size_mismatch is False

    def test_p_value_inconsistency(self):
        summary = ABTestSummary(
            id="test-2",
            url="http://example.com/2",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.01,
            effect_size=0.05
        )
        # Reconstructed p-value is 0.07, diff = 0.06 > 0.05
        reconstructed = {
            "n_control": 1000,
            "n_treatment": 1000,
            "p_value": 0.07,
            "effect_size": 0.05
        }

        record = validate_single_summary(summary, reconstructed)

        assert record.is_inconsistent is True
        assert any("P-value difference" in issue for issue in record.issues)

    def test_effect_size_inconsistency(self):
        summary = ABTestSummary(
            id="test-3",
            url="http://example.com/3",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.03,
            effect_size=0.10
        )
        # Reconstructed effect is 0.16, diff = 0.06, relative = 0.06/0.10 = 0.6 > 0.05
        reconstructed = {
            "n_control": 1000,
            "n_treatment": 1000,
            "p_value": 0.03,
            "effect_size": 0.16
        }

        record = validate_single_summary(summary, reconstructed)

        assert record.is_inconsistent is True
        assert any("Relative effect size" in issue for issue in record.issues)

    def test_sample_size_mismatch(self):
        summary = ABTestSummary(
            id="test-4",
            url="http://example.com/4",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.03,
            effect_size=0.05
        )
        reconstructed = {
            "n_control": 1000,
            "n_treatment": 1200,  # Mismatch
            "p_value": 0.03,
            "effect_size": 0.05
        }

        record = validate_single_summary(summary, reconstructed)

        assert record.sample_size_mismatch is True
        assert record.is_excluded_from_prevalence is True
        assert record.is_inconsistent is True  # Excluded records are marked inconsistent
        assert any("Sample size mismatch" in w for w in record.warnings)

    def test_sample_size_mismatch_control(self):
        summary = ABTestSummary(
            id="test-5",
            url="http://example.com/5",
            domain="example.com",
            n_control=1000,
            n_treatment=1000,
            p_value=0.03,
            effect_size=0.05
        )
        reconstructed = {
            "n_control": 900,  # Mismatch
            "n_treatment": 1000,
            "p_value": 0.03,
            "effect_size": 0.05
        }

        record = validate_single_summary(summary, reconstructed)

        assert record.sample_size_mismatch is True
        assert record.is_excluded_from_prevalence is True


class TestValidateAllSummaries:
    def test_mixed_results(self):
        summaries = [
            ABTestSummary(id="s1", url="u1", domain="d1", n_control=100, n_treatment=100, p_value=0.01, effect_size=0.01),
            ABTestSummary(id="s2", url="u2", domain="d2", n_control=100, n_treatment=100, p_value=0.01, effect_size=0.01),
            ABTestSummary(id="s3", url="u3", domain="d3", n_control=100, n_treatment=100, p_value=0.01, effect_size=0.01)
        ]
        reconstructed = [
            {"n_control": 100, "n_treatment": 100, "p_value": 0.01, "effect_size": 0.01},  # Consistent
            {"n_control": 100, "n_treatment": 100, "p_value": 0.10, "effect_size": 0.01},  # P-value mismatch
            {"n_control": 100, "n_treatment": 200, "p_value": 0.01, "effect_size": 0.01}   # Sample size mismatch
        ]

        records = validate_all_summaries(summaries, reconstructed)

        assert len(records) == 3
        assert records[0].is_inconsistent is False
        assert records[1].is_inconsistent is True
        assert records[2].is_excluded_from_prevalence is True
        assert records[2].is_inconsistent is True


class TestRunValidator:
    def test_full_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            summaries_file = tmp_path / "summaries.json"
            recon_file = tmp_path / "reconstructed.json"
            output_file = tmp_path / "audit_report.json"

            summaries = [
                ABTestSummary(id="t1", url="u1", domain="d1", n_control=100, n_treatment=100, p_value=0.01, effect_size=0.01),
                ABTestSummary(id="t2", url="u2", domain="d2", n_control=100, n_treatment=100, p_value=0.01, effect_size=0.01)
            ]
            reconstructed = [
                {"n_control": 100, "n_treatment": 100, "p_value": 0.01, "effect_size": 0.01},
                {"n_control": 100, "n_treatment": 200, "p_value": 0.01, "effect_size": 0.01}
            ]

            with open(summaries_file, "w") as f:
                json.dump([s.model_dump() for s in summaries], f)

            with open(recon_file, "w") as f:
                json.dump(reconstructed, f)

            records = run_validator(summaries_file, recon_file, output_file)

            assert output_file.exists()
            assert len(records) == 2
            assert records[0].is_excluded_from_prevalence is False
            assert records[1].is_excluded_from_prevalence is True

            # Verify JSON content
            with open(output_file, "r") as f:
                data = json.load(f)
            assert len(data) == 2
            assert data[0]["is_excluded_from_prevalence"] is False
            assert data[1]["is_excluded_from_prevalence"] is True
            assert "data_quality_warning" in data[1]["warnings"][0] or "Sample size mismatch" in data[1]["warnings"][0]
