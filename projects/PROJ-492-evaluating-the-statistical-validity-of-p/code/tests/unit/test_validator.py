"""
Unit tests for the Inconsistency Validator (T025).
Covers FR-004 thresholds and FR-004b sample-size mismatch exclusion.
"""
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    validate_single_summary,
    run_validator,
    THRESHOLD_ABS_P_DIFF,
    THRESHOLD_REL_EFFECT_SIZE,
    check_sample_size_mismatch
)

@pytest.fixture
def binary_summary_valid():
    return ABTestSummary(
        url="https://example.com/test1",
        domain="example.com",
        outcome_type="binary",
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.045,
        reconstructed_p_value=0.042,
        reported_effect_size=0.02,
        reconstructed_effect_size=0.02
    )

@pytest.fixture
def binary_summary_p_diff():
    # P-value difference > 0.05
    return ABTestSummary(
        url="https://example.com/test2",
        domain="example.com",
        outcome_type="binary",
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.01,
        reconstructed_p_value=0.07,  # Diff = 0.06 > 0.05
        reported_effect_size=0.02,
        reconstructed_effect_size=0.02
    )

@pytest.fixture
def binary_summary_es_diff():
    # Effect size difference > 5%
    return ABTestSummary(
        url="https://example.com/test3",
        domain="example.com",
        outcome_type="binary",
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.045,
        reconstructed_p_value=0.042,
        reported_effect_size=0.05,  # Reported 0.05 vs Reconstructed 0.02 -> 150% diff
        reconstructed_effect_size=0.02
    )

@pytest.fixture
def binary_summary_missing_n():
    # Sample size missing -> should trigger warning and exclusion
    return ABTestSummary(
        url="https://example.com/test4",
        domain="example.com",
        outcome_type="binary",
        control_n=None,
        treatment_n=None,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.045,
        reconstructed_p_value=0.042,
        reported_effect_size=0.02,
        reconstructed_effect_size=0.02
    )

@pytest.fixture
def binary_summary_missing_n_no_p():
    # Sample size missing but no reported p-value -> warning but not inconsistent
    return ABTestSummary(
        url="https://example.com/test5",
        domain="example.com",
        outcome_type="binary",
        control_n=None,
        treatment_n=None,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=None,
        reconstructed_p_value=0.042,
        reported_effect_size=0.02,
        reconstructed_effect_size=0.02
    )

def test_valid_summary(binary_summary_valid):
    record = validate_single_summary(binary_summary_valid)
    assert record.status == "consistent"
    assert record.data_quality_warning is None
    assert record.is_excluded_from_prevalence is False
    assert "No inconsistencies detected" in record.reasons

def test_p_value_difference_exceeds_threshold(binary_summary_p_diff):
    record = validate_single_summary(binary_summary_p_diff)
    assert record.status == "inconsistent"
    assert any("Absolute p-value difference" in reason for reason in record.reasons)
    assert record.is_excluded_from_prevalence is False

def test_effect_size_difference_exceeds_threshold(binary_summary_es_diff):
    record = validate_single_summary(binary_summary_es_diff)
    assert record.status == "inconsistent"
    assert any("Relative effect size difference" in reason for reason in record.reasons)
    assert record.is_excluded_from_prevalence is False

def test_sample_size_missing_with_p_value(binary_summary_missing_n):
    record = validate_single_summary(binary_summary_missing_n)
    assert record.status == "inconsistent"
    assert record.data_quality_warning is not None
    assert "Missing sample size" in record.data_quality_warning
    assert record.is_excluded_from_prevalence is True
    assert any("Sample size mismatch prevents p-value verification" in reason for reason in record.reasons)

def test_sample_size_missing_no_p_value(binary_summary_missing_n_no_p):
    record = validate_single_summary(binary_summary_missing_n_no_p)
    assert record.status == "consistent"
    assert record.data_quality_warning is not None
    assert "Missing sample size" in record.data_quality_warning
    assert record.is_excluded_from_prevalence is True
    # Should not be marked inconsistent if no p-value to verify
    assert "No inconsistencies detected" not in record.reasons
    assert any("Sample size data quality issue" in reason for reason in record.reasons)

def test_run_validator_writes_json(binary_summary_valid, binary_summary_p_diff, tmp_path):
    summaries = [binary_summary_valid, binary_summary_p_diff]
    output_file = tmp_path / "audit_report.json"
    
    records = run_validator(summaries, output_file)
    
    assert output_file.exists()
    assert len(records) == 2
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]['status'] == 'consistent'
    assert data[1]['status'] == 'inconsistent'

def test_check_sample_size_mismatch():
    # Valid
    valid_summary = ABTestSummary(
        url="test", domain="test", outcome_type="binary",
        control_n=100, treatment_n=100, control_rate=0.1, treatment_rate=0.11
    )
    is_mismatch, msg = check_sample_size_mismatch(valid_summary)
    assert is_mismatch is False
    assert msg is None

    # Missing N
    missing_n_summary = ABTestSummary(
        url="test", domain="test", outcome_type="binary",
        control_n=None, treatment_n=100, control_rate=0.1, treatment_rate=0.11
    )
    is_mismatch, msg = check_sample_size_mismatch(missing_n_summary)
    assert is_mismatch is True
    assert "Missing sample size" in msg

    # Invalid N
    invalid_n_summary = ABTestSummary(
        url="test", domain="test", outcome_type="binary",
        control_n=0, treatment_n=100, control_rate=0.1, treatment_rate=0.11
    )
    is_mismatch, msg = check_sample_size_mismatch(invalid_n_summary)
    assert is_mismatch is True
    assert "Invalid sample size" in msg
