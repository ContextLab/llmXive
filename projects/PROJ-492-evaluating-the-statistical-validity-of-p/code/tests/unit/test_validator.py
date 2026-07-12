"""
Unit tests for the Inconsistency Validator (T025).

Tests:
1. Absolute p-value difference > 0.05 triggers inconsistency.
2. Relative effect size difference > 5% triggers inconsistency.
3. Sample size mismatch triggers data_quality_warning and exclusion.
4. Combined scenarios.
"""
import pytest
from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    THRESHOLD_ABSOLUTE_P_DIFF,
    THRESHOLD_RELATIVE_EFFECT_SIZE
)
from code.src.models.data_models import ABTestSummary, AuditRecord


def create_summary(
    url="https://example.com/test",
    url_hash="hash123",
    domain="example.com",
    p_value=0.04,
    effect_size=0.1,
    sample_size=1000
):
    return ABTestSummary(
        url=url,
        url_hash=url_hash,
        domain=domain,
        p_value=p_value,
        effect_size=effect_size,
        sample_size=sample_size,
        # Minimal required fields for ABTestSummary
        baseline_rate=0.5,
        treatment_rate=0.6,
        test_type="binary"
    )


def test_p_value_inconsistency():
    """Test that p-value diff > 0.05 flags inconsistency."""
    summary = create_summary(p_value=0.04, effect_size=0.1, sample_size=1000)
    recon = {
        'reconstructed_p_value': 0.12, # Diff = 0.08 > 0.05
        'reconstructed_effect_size': 0.1,
        'reconstructed_sample_size': 1000
    }
    
    record = validate_single_summary(summary, recon)
    
    assert record.is_inconsistent is True
    assert "P-value difference" in str(record.inconsistency_reason)
    assert record.data_quality_warning is False


def test_effect_size_inconsistency():
    """Test that relative effect size diff > 5% flags inconsistency."""
    # Reported 0.10, Reconstructed 0.05 -> Diff = 0.05. Rel Diff = 0.05/0.05 = 100% > 5%
    summary = create_summary(p_value=0.04, effect_size=0.10, sample_size=1000)
    recon = {
        'reconstructed_p_value': 0.04,
        'reconstructed_effect_size': 0.05, 
        'reconstructed_sample_size': 1000
    }
    
    record = validate_single_summary(summary, recon)
    
    assert record.is_inconsistent is True
    assert "Effect size relative difference" in str(record.inconsistency_reason)


def test_sample_size_mismatch_warning():
    """Test that sample size mismatch flags warning and exclusion."""
    summary = create_summary(p_value=0.04, effect_size=0.1, sample_size=1000)
    recon = {
        'reconstructed_p_value': 0.04,
        'reconstructed_effect_size': 0.1,
        'reconstructed_sample_size': 500 # Mismatch
    }
    
    record = validate_single_summary(summary, recon)
    
    assert record.is_inconsistent is False # Not a statistical inconsistency per se
    assert record.data_quality_warning is True
    assert record.exclusion_reason == "sample_size_mismatch"
    assert "Sample size mismatch" in str(record.warning_message)


def test_combined_inconsistency_and_warning():
    """Test both p-value inconsistency and sample size mismatch."""
    summary = create_summary(p_value=0.04, effect_size=0.1, sample_size=1000)
    recon = {
        'reconstructed_p_value': 0.15, # Inconsistent
        'reconstructed_effect_size': 0.1,
        'reconstructed_sample_size': 500 # Mismatch
    }
    
    record = validate_single_summary(summary, recon)
    
    assert record.is_inconsistent is True
    assert record.data_quality_warning is True
    assert record.exclusion_reason == "sample_size_mismatch"


def test_no_inconsistency():
    """Test that consistent values pass without flags."""
    summary = create_summary(p_value=0.04, effect_size=0.1, sample_size=1000)
    recon = {
        'reconstructed_p_value': 0.041, # Diff 0.001 < 0.05
        'reconstructed_effect_size': 0.102, # Rel Diff ~2% < 5%
        'reconstructed_sample_size': 1000
    }
    
    record = validate_single_summary(summary, recon)
    
    assert record.is_inconsistent is False
    assert record.data_quality_warning is False
    assert record.inconsistency_reason is None
    assert record.warning_message is None


def test_validate_all_summaries():
    """Test batch validation logic."""
    summaries = [
        create_summary(url_hash="h1", p_value=0.04, effect_size=0.1, sample_size=1000),
        create_summary(url_hash="h2", p_value=0.04, effect_size=0.1, sample_size=1000),
        create_summary(url_hash="h3", p_value=0.04, effect_size=0.1, sample_size=1000)
    ]
    
    recon_results = [
        {'reconstructed_p_value': 0.15, 'reconstructed_effect_size': 0.1, 'reconstructed_sample_size': 1000}, # Inconsistent
        {'reconstructed_p_value': 0.04, 'reconstructed_effect_size': 0.1, 'reconstructed_sample_size': 500}, # Warning
        {'reconstructed_p_value': 0.04, 'reconstructed_effect_size': 0.1, 'reconstructed_sample_size': 1000}  # OK
    ]
    
    records = validate_all_summaries(summaries, recon_results)
    
    assert len(records) == 3
    assert records[0].is_inconsistent is True
    assert records[0].data_quality_warning is False
    
    assert records[1].is_inconsistent is False
    assert records[1].data_quality_warning is True
    
    assert records[2].is_inconsistent is False
    assert records[2].data_quality_warning is False
