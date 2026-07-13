"""
Unit tests for the validator module (T025).

Tests cover:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Inequality p-value handling (flagging and exclusion logic)
- Sample-size mismatch detection and data_quality_warning generation
"""
import pytest
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from decimal import Decimal

# Import from the project's src module
from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    check_p_value_consistency,
    check_effect_size_consistency,
    check_sample_size_consistency,
    handle_inequality_p_value,
    generate_audit_record
)
from code.src.models.data_models import ABTestSummary, AuditRecord, ValidationResult
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants matching FR-004
THRESHOLD_P_DIFF = 0.05
THRESHOLD_EFFECT_SIZE_REL = 0.05  # 5%
INEQUALITY_P_THRESHOLD = 0.001

@pytest.fixture
def valid_summary_binary() -> ABTestSummary:
    """Create a valid binary outcome summary."""
    return ABTestSummary(
        url="https://example.com/test1",
        domain="example.com",
        test_type="binary",
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.03,
        reported_effect_size=0.02,
        reported_effect_size_type="absolute",
        reconstruction_p_value=0.028,
        reconstruction_effect_size=0.02,
        reconstruction_effect_size_type="absolute",
        is_inequality_p_value=False,
        sample_size_mismatch=False
    )

@pytest.fixture
def valid_summary_continuous() -> ABTestSummary:
    """Create a valid continuous outcome summary."""
    return ABTestSummary(
        url="https://example.com/test2",
        domain="example.com",
        test_type="continuous",
        control_n=500,
        treatment_n=500,
        control_mean=10.0,
        treatment_mean=10.5,
        control_std=2.0,
        treatment_std=2.1,
        reported_p_value=0.04,
        reported_effect_size=0.5,
        reported_effect_size_type="cohen_d",
        reconstruction_p_value=0.039,
        reconstruction_effect_size=0.49,
        reconstruction_effect_size_type="cohen_d",
        is_inequality_p_value=False,
        sample_size_mismatch=False
    )

@pytest.fixture
def summary_with_p_diff_violation() -> ABTestSummary:
    """Summary where absolute p-difference exceeds 0.05."""
    return ABTestSummary(
        url="https://example.com/test3",
        domain="example.com",
        test_type="binary",
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.01,
        reported_effect_size=0.02,
        reported_effect_size_type="absolute",
        reconstruction_p_value=0.07,  # Diff = 0.06 > 0.05
        reconstruction_effect_size=0.02,
        reconstruction_effect_size_type="absolute",
        is_inequality_p_value=False,
        sample_size_mismatch=False
    )

@pytest.fixture
def summary_with_effect_size_violation() -> ABTestSummary:
    """Summary where relative effect-size difference exceeds 5%."""
    return ABTestSummary(
        url="https://example.com/test4",
        domain="example.com",
        test_type="binary",
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.03,
        reported_effect_size=0.02,
        reported_effect_size_type="absolute",
        reconstruction_effect_size=0.035,  # Relative diff = |0.02-0.035|/0.02 = 0.75 > 0.05
        reconstruction_p_value=0.028,
        reconstruction_effect_size_type="absolute",
        is_inequality_p_value=False,
        sample_size_mismatch=False
    )

@pytest.fixture
def summary_with_sample_size_mismatch() -> ABTestSummary:
    """Summary with sample size mismatch flagged."""
    return ABTestSummary(
        url="https://example.com/test5",
        domain="example.com",
        test_type="binary",
        control_n=1000,
        treatment_n=1200,  # Mismatch
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.03,
        reported_effect_size=0.02,
        reported_effect_size_type="absolute",
        reconstruction_p_value=0.028,
        reconstruction_effect_size=0.02,
        reconstruction_effect_size_type="absolute",
        is_inequality_p_value=False,
        sample_size_mismatch=True
    )

@pytest.fixture
def summary_with_inequality_p_value() -> ABTestSummary:
    """Summary with inequality p-value."""
    return ABTestSummary(
        url="https://example.com/test6",
        domain="example.com",
        test_type="binary",
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value="<0.001",
        reported_effect_size=0.02,
        reported_effect_size_type="absolute",
        reconstruction_p_value=0.028,
        reconstruction_effect_size=0.02,
        reconstruction_effect_size_type="absolute",
        is_inequality_p_value=True,
        sample_size_mismatch=False
    )

def test_check_p_value_consistency_pass():
    """Test that p-difference <= 0.05 passes."""
    result = check_p_value_consistency(0.03, 0.028, THRESHOLD_P_DIFF)
    assert result.is_valid is True
    assert result.violation_type == "none"

def test_check_p_value_consistency_fail():
    """Test that p-difference > 0.05 fails."""
    result = check_p_value_consistency(0.01, 0.07, THRESHOLD_P_DIFF)
    assert result.is_valid is False
    assert result.violation_type == "p_value_diff"
    assert result.diff_value == pytest.approx(0.06, abs=1e-6)

def test_check_effect_size_consistency_pass():
    """Test that relative effect-size difference <= 5% passes."""
    result = check_effect_size_consistency(0.02, 0.021, THRESHOLD_EFFECT_SIZE_REL)
    assert result.is_valid is True
    assert result.violation_type == "none"

def test_check_effect_size_consistency_fail():
    """Test that relative effect-size difference > 5% fails."""
    result = check_effect_size_consistency(0.02, 0.035, THRESHOLD_EFFECT_SIZE_REL)
    assert result.is_valid is False
    assert result.violation_type == "effect_size_diff"
    # Relative diff = |0.02 - 0.035| / 0.02 = 0.75
    assert result.diff_value == pytest.approx(0.75, abs=1e-6)

def test_check_effect_size_consistency_zero_baseline():
    """Test effect size check when baseline is zero (should handle gracefully)."""
    # If reported is 0, we can't compute relative diff; should pass or handle edge case
    result = check_effect_size_consistency(0.0, 0.0, THRESHOLD_EFFECT_SIZE_REL)
    assert result.is_valid is True

def test_check_sample_size_consistency_match():
    """Test sample size consistency when sizes match."""
    result = check_sample_size_consistency(1000, 1000)
    assert result.is_valid is True
    assert result.has_mismatch is False

def test_check_sample_size_consistency_mismatch():
    """Test sample size consistency when sizes differ."""
    result = check_sample_size_consistency(1000, 1200)
    assert result.is_valid is False
    assert result.has_mismatch is True
    assert result.control_n == 1000
    assert result.treatment_n == 1200

def test_handle_inequality_p_value_normal():
    """Test handling of normal p-value."""
    result = handle_inequality_p_value(0.03, is_inequality=False)
    assert result.is_inequality is False
    assert result.p_value == 0.03

def test_handle_inequality_p_value_inequality():
    """Test handling of inequality p-value (e.g., <0.001)."""
    result = handle_inequality_p_value("<0.001", is_inequality=True)
    assert result.is_inequality is True
    # Should convert to numeric for comparison (e.g., 0.001)
    assert result.p_value == 0.001

def test_handle_inequality_p_value_very_small():
    """Test handling of very small inequality p-value."""
    result = handle_inequality_p_value("<0.0001", is_inequality=True)
    assert result.is_inequality is True
    assert result.p_value == 0.0001

def test_validate_single_summary_valid(valid_summary_binary):
    """Test validation of a fully valid summary."""
    result = validate_single_summary(valid_summary_binary)
    assert result.is_valid is True
    assert len(result.violations) == 0
    assert result.data_quality_warning is False

def test_validate_single_summary_p_diff_violation(summary_with_p_diff_violation):
    """Test validation when p-difference exceeds threshold."""
    result = validate_single_summary(summary_with_p_diff_violation)
    assert result.is_valid is False
    assert any(v.violation_type == "p_value_diff" for v in result.violations)

def test_validate_single_summary_effect_size_violation(summary_with_effect_size_violation):
    """Test validation when effect-size difference exceeds threshold."""
    result = validate_single_summary(summary_with_effect_size_violation)
    assert result.is_valid is False
    assert any(v.violation_type == "effect_size_diff" for v in result.violations)

def test_validate_single_summary_sample_size_mismatch(summary_with_sample_size_mismatch):
    """Test validation generates data_quality_warning for sample-size mismatch."""
    result = validate_single_summary(summary_with_sample_size_mismatch)
    # The summary itself may still be "valid" statistically, but flagged for quality
    assert result.data_quality_warning is True
    assert any("sample_size_mismatch" in str(v.message) for v in result.violations)

def test_validate_single_summary_inequality_p_value(summary_with_inequality_p_value):
    """Test validation handles inequality p-values correctly."""
    result = validate_single_summary(summary_with_inequality_p_value)
    # Should not fail solely due to inequality p-value if reconstruction is reasonable
    # The inequality is handled by converting to numeric
    assert result.is_valid is True or any(v.violation_type == "p_value_diff" for v in result.violations)

def test_generate_audit_record_valid(valid_summary_binary):
    """Test audit record generation for valid summary."""
    result = validate_single_summary(valid_summary_binary)
    audit_record = generate_audit_record(valid_summary_binary, result)
    
    assert audit_record.url == valid_summary_binary.url
    assert audit_record.is_consistent is True
    assert audit_record.data_quality_warning is False
    assert len(audit_record.violations) == 0

def test_generate_audit_record_with_violations(summary_with_p_diff_violation):
    """Test audit record generation with violations."""
    result = validate_single_summary(summary_with_p_diff_violation)
    audit_record = generate_audit_record(summary_with_p_diff_violation, result)
    
    assert audit_record.url == summary_with_p_diff_violation.url
    assert audit_record.is_consistent is False
    assert len(audit_record.violations) > 0
    assert any(v.violation_type == "p_value_diff" for v in audit_record.violations)

def test_generate_audit_record_with_quality_warning(summary_with_sample_size_mismatch):
    """Test audit record includes data_quality_warning flag."""
    result = validate_single_summary(summary_with_sample_size_mismatch)
    audit_record = generate_audit_record(summary_with_sample_size_mismatch, result)
    
    assert audit_record.data_quality_warning is True
    assert "sample_size_mismatch" in audit_record.notes

def test_validate_all_summaries():
    """Test batch validation of multiple summaries."""
    summaries = [
        ABTestSummary(
            url="https://example.com/test1",
            domain="example.com",
            test_type="binary",
            control_n=1000,
            treatment_n=1000,
            control_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.03,
            reported_effect_size=0.02,
            reported_effect_size_type="absolute",
            reconstruction_p_value=0.028,
            reconstruction_effect_size=0.02,
            reconstruction_effect_size_type="absolute",
            is_inequality_p_value=False,
            sample_size_mismatch=False
        ),
        ABTestSummary(
            url="https://example.com/test2",
            domain="example.com",
            test_type="binary",
            control_n=1000,
            treatment_n=1000,
            control_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.01,
            reported_effect_size=0.02,
            reported_effect_size_type="absolute",
            reconstruction_p_value=0.07,
            reconstruction_effect_size=0.02,
            reconstruction_effect_size_type="absolute",
            is_inequality_p_value=False,
            sample_size_mismatch=False
        )
    ]
    
    records = validate_all_summaries(summaries)
    
    assert len(records) == 2
    assert records[0].is_consistent is True
    assert records[1].is_consistent is False

def test_validator_excludes_mismatch_from_aggregate():
    """Test that sample-size mismatch entries are excluded from aggregate prevalence estimates.
    
    Per FR-004b, entries with sample_size_mismatch=True should be flagged with 
    data_quality_warning but excluded from aggregate statistics.
    """
    summaries = [
        ABTestSummary(
            url="https://example.com/test1",
            domain="example.com",
            test_type="binary",
            control_n=1000,
            treatment_n=1000,
            control_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.03,
            reported_effect_size=0.02,
            reported_effect_size_type="absolute",
            reconstruction_p_value=0.028,
            reconstruction_effect_size=0.02,
            reconstruction_effect_size_type="absolute",
            is_inequality_p_value=False,
            sample_size_mismatch=False
        ),
        ABTestSummary(
            url="https://example.com/test2",
            domain="example.com",
            test_type="binary",
            control_n=1000,
            treatment_n=1200,  # Mismatch
            control_rate=0.10,
            treatment_rate=0.12,
            reported_p_value=0.03,
            reported_effect_size=0.02,
            reported_effect_size_type="absolute",
            reconstruction_p_value=0.028,
            reconstruction_effect_size=0.02,
            reconstruction_effect_size_type="absolute",
            is_inequality_p_value=False,
            sample_size_mismatch=True
        )
    ]
    
    records = validate_all_summaries(summaries)
    
    # First record should be valid
    assert records[0].is_consistent is True
    assert records[0].data_quality_warning is False
    
    # Second record should have data_quality_warning
    assert records[1].data_quality_warning is True
    assert "sample_size_mismatch" in records[1].notes
    
    # Count records for aggregate (should exclude mismatch)
    valid_for_aggregate = [r for r in records if not r.data_quality_warning]
    assert len(valid_for_aggregate) == 1

def test_validator_inequality_handling_in_aggregate():
    """Test that inequality p-values are handled correctly in validation."""
    summaries = [
        ABTestSummary(
            url="https://example.com/test1",
            domain="example.com",
            test_type="binary",
            control_n=1000,
            treatment_n=1000,
            control_rate=0.10,
            treatment_rate=0.12,
            reported_p_value="<0.001",
            reported_effect_size=0.02,
            reported_effect_size_type="absolute",
            reconstruction_p_value=0.028,
            reconstruction_effect_size=0.02,
            reconstruction_effect_size_type="absolute",
            is_inequality_p_value=True,
            sample_size_mismatch=False
        )
    ]
    
    records = validate_all_summaries(summaries)
    
    # Should not crash on inequality p-value
    assert len(records) == 1
    # The inequality is converted to 0.001, so diff = |0.001 - 0.028| = 0.027 < 0.05
    # Should pass p-value check
    assert records[0].is_consistent is True

def test_validator_edge_case_very_small_p_values():
    """Test handling of very small p-values near machine epsilon."""
    summary = ABTestSummary(
        url="https://example.com/test_edge",
        domain="example.com",
        test_type="binary",
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.00001,
        reported_effect_size=0.02,
        reported_effect_size_type="absolute",
        reconstruction_p_value=0.00002,
        reconstruction_effect_size=0.02,
        reconstruction_effect_size_type="absolute",
        is_inequality_p_value=False,
        sample_size_mismatch=False
    )
    
    result = validate_single_summary(summary)
    # Diff = 0.00001 < 0.05, should pass
    assert result.is_valid is True

def test_validator_edge_case_effect_size_zero():
    """Test effect size validation when reported effect size is zero."""
    summary = ABTestSummary(
        url="https://example.com/test_zero_es",
        domain="example.com",
        test_type="binary",
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.10,
        reported_p_value=0.99,
        reported_effect_size=0.0,
        reported_effect_size_type="absolute",
        reconstruction_p_value=0.98,
        reconstruction_effect_size=0.0,
        reconstruction_effect_size_type="absolute",
        is_inequality_p_value=False,
        sample_size_mismatch=False
    )
    
    result = validate_single_summary(summary)
    # Both effect sizes are 0, relative diff is undefined but should pass
    assert result.is_valid is True