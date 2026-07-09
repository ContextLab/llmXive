"""
Unit tests for the inconsistency validator (T025).

Tests:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Sample-size mismatch detection and exclusion
- data_quality_warning generation
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    filter_for_prevalence,
    write_audit_report,
    check_sample_size_consistency,
    compute_effect_size,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD
)
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.config import SEED

# Test fixtures
@pytest.fixture
def valid_summary():
    return ABTestSummary(
        url="https://example.com/test1",
        domain="example.com",
        year=2023,
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.03,
        test_type="binary"
    )

@pytest.fixture
def summary_with_sample_mismatch():
    return ABTestSummary(
        url="https://example.com/test2",
        domain="example.com",
        year=2023,
        control_n=1000,
        treatment_n=800,  # 20% smaller - should trigger mismatch
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.03,
        test_type="binary"
    )

@pytest.fixture
def summary_with_p_value_mismatch():
    return ABTestSummary(
        url="https://example.com/test3",
        domain="example.com",
        year=2023,
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.01,  # Reported is 0.01
        test_type="binary"
    )

@pytest.fixture
def summary_with_effect_size_mismatch():
    return ABTestSummary(
        url="https://example.com/test4",
        domain="example.com",
        year=2023,
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,  # Effect size = 20%
        reported_p_value=0.03,
        test_type="binary"
    )

def test_effect_size_calculation(valid_summary):
    """Test that effect size is calculated correctly."""
    effect = compute_effect_size(valid_summary)
    # (0.12 - 0.10) / 0.10 = 0.20
    assert effect == pytest.approx(0.20, rel=1e-6)

def test_effect_size_zero_control():
    """Test effect size calculation with zero control rate."""
    summary = ABTestSummary(
        url="https://example.com/test",
        domain="example.com",
        year=2023,
        control_n=1000,
        treatment_n=1000,
        control_rate=0.0,
        treatment_rate=0.12,
        reported_p_value=0.03,
        test_type="binary"
    )
    effect = compute_effect_size(summary)
    assert effect is None

def test_sample_size_consistency_check(valid_summary):
    """Test sample size consistency check with matching sizes."""
    is_consistent, warning = check_sample_size_consistency(valid_summary)
    assert is_consistent is True
    assert warning is None

def test_sample_size_mismatch_detection(summary_with_sample_mismatch):
    """Test that sample size mismatch is detected."""
    is_consistent, warning = check_sample_size_consistency(summary_with_sample_mismatch)
    assert is_consistent is False
    assert warning is not None
    assert "Sample size mismatch" in warning

def test_sample_size_missing_data():
    """Test sample size check with missing data."""
    summary = ABTestSummary(
        url="https://example.com/test",
        domain="example.com",
        year=2023,
        control_n=None,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.03,
        test_type="binary"
    )
    is_consistent, warning = check_sample_size_consistency(summary)
    assert is_consistent is True  # Cannot determine, so not flagged
    assert warning is None

def test_p_value_threshold_violation(summary_with_p_value_mismatch):
    """Test that p-value discrepancy > 0.05 is flagged."""
    # Simulate reconstruction that gives p=0.07 (diff = 0.06 > 0.05)
    reconstructed_results = {
        "https://example.com/test3": {"p_value": 0.07, "effect_size": 0.20}
    }
    
    record = validate_single_summary(summary_with_p_value_mismatch, 0.07, 0.20)
    
    assert record.is_inconsistent is True
    assert any("P-value discrepancy" in reason for reason in record.reasons)
    assert record.inconsistency_type == "p_value_mismatch"

def test_effect_size_threshold_violation(summary_with_effect_size_mismatch):
    """Test that effect size discrepancy > 5% is flagged."""
    # Reported effect size = 20%
    # Simulate reconstruction that gives 25% (relative diff = 5/20 = 25% > 5%)
    reconstructed_results = {
        "https://example.com/test4": {"p_value": 0.03, "effect_size": 0.25}
    }
    
    record = validate_single_summary(summary_with_effect_size_mismatch, 0.03, 0.25)
    
    assert record.is_inconsistent is True
    assert any("Effect size discrepancy" in reason for reason in record.reasons)
    assert record.inconsistency_type == "effect_size_mismatch"

def test_data_quality_warning_generation(summary_with_sample_mismatch):
    """Test that data_quality_warning is generated for sample-size mismatch."""
    reconstructed_results = {
        "https://example.com/test2": {"p_value": 0.03, "effect_size": 0.20}
    }
    
    record = validate_single_summary(summary_with_sample_mismatch, 0.03, 0.20)
    
    assert len(record.data_quality_warnings) > 0
    assert any("Sample size mismatch" in warning for warning in record.data_quality_warnings)

def test_filter_for_prevalence_excludes_mismatches(
    valid_summary,
    summary_with_sample_mismatch,
    summary_with_p_value_mismatch
):
    """Test that filter_for_prevalence excludes sample-size mismatch entries."""
    # Create audit records
    recon_results = {
        "https://example.com/test1": {"p_value": 0.03, "effect_size": 0.20},
        "https://example.com/test2": {"p_value": 0.03, "effect_size": 0.20},
        "https://example.com/test3": {"p_value": 0.07, "effect_size": 0.20}
    }
    
    records = validate_all_summaries(
        [valid_summary, summary_with_sample_mismatch, summary_with_p_value_mismatch],
        recon_results
    )
    
    # Filter for prevalence
    filtered = filter_for_prevalence(records)
    
    # Should exclude the sample-size mismatch record
    assert len(filtered) == 2
    urls_in_filtered = {r.url for r in filtered}
    assert "https://example.com/test2" not in urls_in_filtered
    # Should include the p-value mismatch (it's inconsistent but not a data quality issue)
    assert "https://example.com/test3" in urls_in_filtered

def test_write_audit_report(tmp_path):
    """Test that write_audit_report creates valid JSON."""
    summary = ABTestSummary(
        url="https://example.com/test",
        domain="example.com",
        year=2023,
        control_n=1000,
        treatment_n=1000,
        control_rate=0.10,
        treatment_rate=0.12,
        reported_p_value=0.03,
        test_type="binary"
    )
    
    records = [
        AuditRecord(
            url=summary.url,
            domain=summary.domain,
            year=summary.year,
            is_inconsistent=False,
            inconsistency_type=None,
            reasons=[],
            data_quality_warnings=[],
            reported_p_value=summary.reported_p_value,
            reconstructed_p_value=0.03,
            reported_effect_size=0.20,
            reconstructed_effect_size=0.20,
            sample_size_consistent=True,
            validation_timestamp=datetime.utcnow().isoformat(),
            seed_used=SEED
        )
    ]
    
    output_path = tmp_path / "audit_report.json"
    write_audit_report(records, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data["total_records"] == 1
    assert data["inconsistent_count"] == 0
    assert len(data["records"]) == 1
    assert data["records"][0]["url"] == "https://example.com/test"

def test_no_p_value_inconsistency_when_within_threshold(valid_summary):
    """Test that p-value differences <= 0.05 are not flagged."""
    # Reported = 0.03, Reconstructed = 0.05 (diff = 0.02 <= 0.05)
    record = validate_single_summary(valid_summary, 0.05, 0.20)
    
    # Should not be inconsistent due to p-value
    p_value_reasons = [r for r in record.reasons if "P-value discrepancy" in r]
    assert len(p_value_reasons) == 0

def test_no_effect_size_inconsistency_when_within_threshold(valid_summary):
    """Test that effect size differences <= 5% are not flagged."""
    # Reported effect = 20%, Reconstructed = 20.5% (relative diff = 0.5/20 = 2.5% <= 5%)
    record = validate_single_summary(valid_summary, 0.03, 0.205)
    
    # Should not be inconsistent due to effect size
    effect_reasons = [r for r in record.reasons if "Effect size discrepancy" in r]
    assert len(effect_reasons) == 0