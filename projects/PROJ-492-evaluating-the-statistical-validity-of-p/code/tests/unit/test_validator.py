"""
Unit tests for the validator module (T025).
Tests FR-004 thresholds and FR-004b sample-size exclusion.
"""

import json
import math
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
import numpy as np

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
    write_audit_report,
    ABSOLUTE_P_THRESHOLD,
    RELATIVE_EFFECT_SIZE_THRESHOLD,
)

def test_calculate_absolute_p_difference():
    assert calculate_absolute_p_difference(0.04, 0.03) == 0.01
    assert calculate_absolute_p_difference(0.01, 0.07) == 0.06
    assert calculate_absolute_p_difference(0.05, 0.05) == 0.0

def test_calculate_relative_effect_size_difference():
    # Basic case
    assert math.isclose(calculate_relative_effect_size_difference(0.10, 0.10), 0.0)
    # 50% relative difference: |0.15 - 0.10| / 0.10 = 0.5
    assert math.isclose(calculate_relative_effect_size_difference(0.15, 0.10), 0.5)
    # Negative effect sizes
    assert math.isclose(calculate_relative_effect_size_difference(-0.10, -0.10), 0.0)
    # Zero reconstructed effect
    assert calculate_relative_effect_size_difference(0.10, 0.0) == float('inf')
    assert calculate_relative_effect_size_difference(0.0, 0.0) == 0.0

def test_check_p_value_consistency():
    # Consistent: diff 0.01 <= 0.05
    is_cons, diff = check_p_value_consistency(0.04, 0.03)
    assert is_cons is True
    assert math.isclose(diff, 0.01)

    # Inconsistent: diff 0.06 > 0.05
    is_cons, diff = check_p_value_consistency(0.01, 0.07)
    assert is_cons is False
    assert math.isclose(diff, 0.06)

    # None values
    is_cons, diff = check_p_value_consistency(None, 0.05)
    assert is_cons is False
    assert math.isnan(diff)

def test_check_effect_size_consistency():
    # Consistent: 5% diff
    is_cons, diff = check_effect_size_consistency(0.105, 0.10)
    assert is_cons is True
    assert math.isclose(diff, 0.05)

    # Inconsistent: > 5% diff
    is_cons, diff = check_effect_size_consistency(0.11, 0.10)
    assert is_cons is False
    assert math.isclose(diff, 0.1)

    # None values
    is_cons, diff = check_effect_size_consistency(None, 0.10)
    assert is_cons is False
    assert math.isnan(diff)

def test_detect_sample_size_mismatch():
    # Valid sample sizes
    summary = ABTestSummary(
        url="http://example.com",
        domain="example.com",
        year=2023,
        reported_p_value=0.04,
        reported_effect_size=0.05,
        sample_size_a=1000,
        sample_size_b=1000,
    )
    assert detect_sample_size_mismatch(summary) is False

    # Missing sample size
    summary_missing = ABTestSummary(
        url="http://example.com",
        domain="example.com",
        year=2023,
        reported_p_value=0.04,
        reported_effect_size=0.05,
        sample_size_a=None,
        sample_size_b=1000,
    )
    assert detect_sample_size_mismatch(summary_missing) is True

    # Zero sample size
    summary_zero = ABTestSummary(
        url="http://example.com",
        domain="example.com",
        year=2023,
        reported_p_value=0.04,
        reported_effect_size=0.05,
        sample_size_a=0,
        sample_size_b=1000,
    )
    assert detect_sample_size_mismatch(summary_zero) is True

def test_create_audit_record_p_inconsistent():
    summary = ABTestSummary(
        url="http://example.com",
        domain="example.com",
        year=2023,
        reported_p_value=0.01,
        reported_effect_size=0.05,
        sample_size_a=1000,
        sample_size_b=1000,
    )
    # P-value diff 0.06 > 0.05
    record = create_audit_record(summary, False, 0.06, True, 0.0, False)
    assert record.is_inconsistent is True
    assert any("P-value difference" in issue for issue in record.issues)
    assert record.data_quality_warning is None

def test_create_audit_record_effect_inconsistent():
    summary = ABTestSummary(
        url="http://example.com",
        domain="example.com",
        year=2023,
        reported_p_value=0.04,
        reported_effect_size=0.10,
        sample_size_a=1000,
        sample_size_b=1000,
    )
    # Effect diff 0.10 > 0.05
    record = create_audit_record(summary, True, 0.0, False, 0.10, False)
    assert record.is_inconsistent is True
    assert any("Effect size" in issue for issue in record.issues)

def test_create_audit_record_sample_size_mismatch():
    summary = ABTestSummary(
        url="http://example.com",
        domain="example.com",
        year=2023,
        reported_p_value=0.04,
        reported_effect_size=0.05,
        sample_size_a=None,
        sample_size_b=1000,
    )
    record = create_audit_record(summary, True, 0.0, True, 0.0, True)
    assert record.is_inconsistent is True  # Marked inconsistent due to data quality
    assert record.data_quality_warning is not None
    assert any("Sample size mismatch" in w for w in record.data_quality_warning)

def test_validate_summary():
    summary = ABTestSummary(
        url="http://example.com",
        domain="example.com",
        year=2023,
        reported_p_value=0.01,
        reported_effect_size=0.05,
        sample_size_a=1000,
        sample_size_b=1000,
    )
    # Mock reconstructed values to trigger inconsistency
    summary.reconstructed_p_value = 0.07  # Diff 0.06
    summary.reconstructed_effect_size = 0.05

    record = validate_summary(summary)
    assert record.is_inconsistent is True
    assert any("P-value difference" in issue for issue in record.issues)

def test_validate_all_summaries():
    summaries = [
        ABTestSummary(
            url="http://example.com/1",
            domain="example.com",
            year=2023,
            reported_p_value=0.04,
            reported_effect_size=0.05,
            sample_size_a=1000,
            sample_size_b=1000,
        ),
        ABTestSummary(
            url="http://example.com/2",
            domain="example.com",
            year=2023,
            reported_p_value=0.01,
            reported_effect_size=0.05,
            sample_size_a=1000,
            sample_size_b=1000,
        ),
    ]
    # Set reconstructed values
    summaries[0].reconstructed_p_value = 0.03  # Consistent
    summaries[0].reconstructed_effect_size = 0.05
    summaries[1].reconstructed_p_value = 0.07  # Inconsistent
    summaries[1].reconstructed_effect_size = 0.05

    records = validate_all_summaries(summaries)
    assert len(records) == 2
    assert records[0].is_inconsistent is False
    assert records[1].is_inconsistent is True

def test_filter_for_prevalence():
    # Create records
    record_ok = AuditRecord(
        url="http://ok.com",
        domain="ok.com",
        year=2023,
        reported_p_value=0.04,
        reconstructed_p_value=0.03,
        reported_effect_size=0.05,
        reconstructed_effect_size=0.05,
        is_inconsistent=False,
        p_value_difference=0.01,
        effect_size_difference=0.0,
        data_quality_warning=None,
        issues=None,
        timestamp=datetime.utcnow().isoformat(),
    )
    record_bad_sample = AuditRecord(
        url="http://bad.com",
        domain="bad.com",
        year=2023,
        reported_p_value=0.04,
        reconstructed_p_value=None,
        reported_effect_size=0.05,
        reconstructed_effect_size=None,
        is_inconsistent=True,
        p_value_difference=0.0,
        effect_size_difference=0.0,
        data_quality_warning=["Sample size mismatch detected; excluded from prevalence estimates (FR-004b)"],
        issues=["Sample size mismatch prevents reliable statistical validation"],
        timestamp=datetime.utcnow().isoformat(),
    )

    records = [record_ok, record_bad_sample]
    filtered = filter_for_prevalence(records)
    assert len(filtered) == 1
    assert filtered[0].url == "http://ok.com"

def test_write_audit_report():
    summaries = [
        ABTestSummary(
            url="http://example.com",
            domain="example.com",
            year=2023,
            reported_p_value=0.04,
            reported_effect_size=0.05,
            sample_size_a=1000,
            sample_size_b=1000,
        )
    ]
    summaries[0].reconstructed_p_value = 0.03
    summaries[0].reconstructed_effect_size = 0.05

    records = validate_all_summaries(summaries)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "audit_report.json"
        write_audit_report(records, output_path)
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["url"] == "http://example.com"
        assert data[0]["is_inconsistent"] is False
        assert data[0]["data_quality_warning"] is None
