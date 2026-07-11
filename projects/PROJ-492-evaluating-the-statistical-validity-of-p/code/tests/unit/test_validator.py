"""
Unit tests for the inconsistency validator (T025).
"""
import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    check_sample_size_mismatch,
    validate_p_value_consistency,
    validate_effect_size_consistency,
    validate_single_summary,
    validate_all,
    write_audit_report,
    run_validator,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD
)

@pytest.fixture
def valid_summary():
    return ABTestSummary(
        id="test-001",
        url="https://example.com/test",
        domain="example.com",
        reported_p_value=0.03,
        reconstructed_p_value=0.032,
        reported_effect_size=0.15,
        reconstructed_effect_size=0.14,
        sample_size_control=1000,
        sample_size_treatment=1000,
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.15
    )

@pytest.fixture
def summary_with_p_mismatch():
    return ABTestSummary(
        id="test-002",
        url="https://example.com/test2",
        domain="example.com",
        reported_p_value=0.01,
        reconstructed_p_value=0.07,  # Diff = 0.06 > 0.05
        reported_effect_size=0.15,
        reconstructed_effect_size=0.14,
        sample_size_control=1000,
        sample_size_treatment=1000,
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.15
    )

@pytest.fixture
def summary_with_effect_mismatch():
    return ABTestSummary(
        id="test-003",
        url="https://example.com/test3",
        domain="example.com",
        reported_p_value=0.03,
        reconstructed_p_value=0.032,
        reported_effect_size=0.20,  # 33% diff from 0.15
        reconstructed_effect_size=0.15,
        sample_size_control=1000,
        sample_size_treatment=1000,
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.15
    )

@pytest.fixture
def summary_with_sample_mismatch():
    return ABTestSummary(
        id="test-004",
        url="https://example.com/test4",
        domain="example.com",
        reported_p_value=0.03,
        reconstructed_p_value=0.032,
        reported_effect_size=0.15,
        reconstructed_effect_size=0.14,
        sample_size_control=1000,
        sample_size_treatment=1500,  # 50% diff
        baseline_conversion_rate=0.10,
        treatment_conversion_rate=0.15
    )

def test_sample_size_no_mismatch(valid_summary):
    is_mismatch, msg = check_sample_size_mismatch(valid_summary)
    assert not is_mismatch
    assert msg is None

def test_sample_size_mismatch(summary_with_sample_mismatch):
    is_mismatch, msg = check_sample_size_mismatch(summary_with_sample_mismatch)
    assert is_mismatch
    assert "Sample size mismatch" in msg

def test_p_value_consistency_pass(valid_summary):
    is_inconsistent, diff = validate_p_value_consistency(valid_summary)
    assert not is_inconsistent
    assert diff is None or diff <= P_VALUE_THRESHOLD

def test_p_value_consistency_fail(summary_with_p_mismatch):
    is_inconsistent, diff = validate_p_value_consistency(summary_with_p_mismatch)
    assert is_inconsistent
    assert diff is not None
    assert diff > P_VALUE_THRESHOLD

def test_effect_size_consistency_pass(valid_summary):
    is_inconsistent, diff = validate_effect_size_consistency(valid_summary)
    assert not is_inconsistent

def test_effect_size_consistency_fail(summary_with_effect_mismatch):
    is_inconsistent, diff = validate_effect_size_consistency(summary_with_effect_mismatch)
    assert is_inconsistent
    assert diff is not None
    assert diff > EFFECT_SIZE_RELATIVE_THRESHOLD

def test_validate_single_summary_no_issues(valid_summary):
    record = validate_single_summary(valid_summary)
    assert not record.is_inconsistent
    assert not record.data_quality_warning
    assert len(record.reasons) == 0
    assert len(record.warnings) == 0

def test_validate_single_summary_p_issue(summary_with_p_mismatch):
    record = validate_single_summary(summary_with_p_mismatch)
    assert record.is_inconsistent
    assert "P_VALUE_MISMATCH" in record.reasons
    assert any("P-value difference" in w for w in record.warnings)

def test_validate_single_summary_effect_issue(summary_with_effect_mismatch):
    record = validate_single_summary(summary_with_effect_mismatch)
    assert record.is_inconsistent
    assert "EFFECT_SIZE_MISMATCH" in record.reasons

def test_validate_single_summary_sample_issue(summary_with_sample_mismatch):
    record = validate_single_summary(summary_with_sample_mismatch)
    # Sample mismatch alone does not make it "inconsistent" per FR-004 (which is about p/eff)
    # But it should trigger a data_quality_warning
    assert not record.is_inconsistent  # Only p or eff mismatch triggers this
    assert record.data_quality_warning
    assert "SAMPLE_SIZE_MISMATCH" in record.reasons
    assert any("Sample size mismatch" in w for w in record.warnings)

def test_validate_all_multiple_summaries(valid_summary, summary_with_p_mismatch, summary_with_sample_mismatch):
    summaries = [valid_summary, summary_with_p_mismatch, summary_with_sample_mismatch]
    records = validate_all(summaries)
    assert len(records) == 3
    assert not records[0].is_inconsistent
    assert records[1].is_inconsistent
    assert records[2].data_quality_warning

def test_write_audit_report(tmp_path):
    summaries = [
        ABTestSummary(
            id="test-001",
            url="https://example.com/test",
            domain="example.com",
            reported_p_value=0.01,
            reconstructed_p_value=0.07,
            reported_effect_size=0.15,
            reconstructed_effect_size=0.14,
            sample_size_control=1000,
            sample_size_treatment=1000,
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.15
        )
    ]
    records = validate_all(summaries)
    output_file = tmp_path / "audit_report.json"
    write_audit_report(records, output_file)

    assert output_file.exists()
    with open(output_file, 'r') as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["is_inconsistent"] is True
    assert "P_VALUE_MISMATCH" in data[0]["reasons"]

def test_run_validator_integration(tmp_path):
    # Create input file
    input_file = tmp_path / "reconstructed_summaries.json"
    summaries = [
        ABTestSummary(
            id="test-001",
            url="https://example.com/test",
            domain="example.com",
            reported_p_value=0.01,
            reconstructed_p_value=0.07,
            reported_effect_size=0.15,
            reconstructed_effect_size=0.14,
            sample_size_control=1000,
            sample_size_treatment=1000,
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.15
        ),
        ABTestSummary(
            id="test-002",
            url="https://example.com/test2",
            domain="example.com",
            reported_p_value=0.03,
            reconstructed_p_value=0.032,
            reported_effect_size=0.15,
            reconstructed_effect_size=0.14,
            sample_size_control=1000,
            sample_size_treatment=1500,
            baseline_conversion_rate=0.10,
            treatment_conversion_rate=0.15
        )
    ]
    with open(input_file, 'w') as f:
        json.dump([s.model_dump() for s in summaries], f)

    output_file = tmp_path / "audit_report.json"
    records = run_validator(input_file, output_file)

    assert output_file.exists()
    assert len(records) == 2
    assert records[0].is_inconsistent
    assert not records[1].is_inconsistent
    assert records[1].data_quality_warning
