"""
Unit tests for the validator module.

Tests cover:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Sample-size mismatch detection and exclusion from prevalence
- Data quality warning generation
"""
import pytest
from pathlib import Path
import json
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
    write_audit_report,
    filter_for_prevalence,
    P_DIFFERENCE_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD
)

@pytest.fixture
def sample_summary():
    return ABTestSummary(
        url="https://example.com/test1",
        domain="example.com",
        publication_year=2023,
        outcome_type="binary",
        p_value=0.03,
        effect_size=0.15,
        sample_size_control=500,
        sample_size_treatment=500,
        total_sample_size=1000,
        baseline_rate=0.10,
        treatment_rate=0.25
    )

@pytest.fixture
def sample_summary_mismatch():
    """Summary with sample size mismatch"""
    return ABTestSummary(
        url="https://example.com/test2",
        domain="example.com",
        publication_year=2023,
        outcome_type="binary",
        p_value=0.04,
        effect_size=0.12,
        sample_size_control=500,
        sample_size_treatment=500,
        total_sample_size=1100,  # Mismatch: should be 1000
        baseline_rate=0.10,
        treatment_rate=0.22
    )

def test_calculate_absolute_p_difference():
    """Test absolute p-difference calculation"""
    diff = calculate_absolute_p_difference(0.03, 0.08)
    assert abs(diff - 0.05) < 1e-10
    
    diff = calculate_absolute_p_difference(0.01, 0.07)
    assert abs(diff - 0.06) < 1e-10

def test_calculate_absolute_p_difference_missing():
    """Test handling of missing p-values"""
    assert np.isnan(calculate_absolute_p_difference(None, 0.05))
    assert np.isnan(calculate_absolute_p_difference(0.05, None))
    assert np.isnan(calculate_absolute_p_difference(None, None))

def test_calculate_relative_effect_size_difference():
    """Test relative effect size difference calculation"""
    diff = calculate_relative_effect_size_difference(0.10, 0.11)
    assert abs(diff - 0.10) < 1e-10  # 10% relative difference
    
    diff = calculate_relative_effect_size_difference(0.20, 0.19)
    assert abs(diff - 0.05) < 1e-10  # 5% relative difference

def test_calculate_relative_effect_size_difference_missing():
    """Test handling of missing effect sizes"""
    assert np.isnan(calculate_relative_effect_size_difference(None, 0.10))
    assert np.isnan(calculate_relative_effect_size_difference(0.10, None))
    assert np.isnan(calculate_relative_effect_size_difference(None, None))

def test_calculate_relative_effect_size_difference_zero():
    """Test handling of zero effect size (division by zero)"""
    assert np.isnan(calculate_relative_effect_size_difference(0.0, 0.05))
    assert np.isnan(calculate_relative_effect_size_difference(0.0, 0.0))

def test_detect_sample_size_mismatch_false(sample_summary):
    """Test detection when no mismatch exists"""
    assert not detect_sample_size_mismatch(sample_summary)

def test_detect_sample_size_mismatch_true(sample_summary_mismatch):
    """Test detection when mismatch exists"""
    assert detect_sample_size_mismatch(sample_summary_mismatch)

def test_detect_sample_size_mismatch_missing_total(sample_summary):
    """Test handling of missing total sample size"""
    summary = sample_summary.model_copy(update={'total_sample_size': None})
    assert not detect_sample_size_mismatch(summary)

def test_check_p_value_consistency_consistent(sample_summary):
    """Test p-value consistency when within threshold"""
    # Reconstructed p = 0.05, reported = 0.03, diff = 0.02 < 0.05
    is_consistent, diff = check_p_value_consistency(sample_summary, 0.05)
    assert is_consistent
    assert abs(diff - 0.02) < 1e-10

def test_check_p_value_consistency_inconsistent(sample_summary):
    """Test p-value consistency when exceeding threshold"""
    # Reconstructed p = 0.10, reported = 0.03, diff = 0.07 > 0.05
    is_consistent, diff = check_p_value_consistency(sample_summary, 0.10)
    assert not is_consistent
    assert abs(diff - 0.07) < 1e-10

def test_check_p_value_consistency_missing():
    """Test handling of missing p-values"""
    summary = ABTestSummary(
        url="test", domain="test.com", publication_year=2023,
        outcome_type="binary", p_value=None, effect_size=0.1,
        sample_size_control=100, sample_size_treatment=100,
        total_sample_size=200, baseline_rate=0.1, treatment_rate=0.2
    )
    is_consistent, diff = check_p_value_consistency(summary, 0.05)
    assert is_consistent
    assert diff is None

def test_check_effect_size_consistency_consistent(sample_summary):
    """Test effect size consistency when within threshold"""
    # Reconstructed = 0.1575 (5% higher than 0.15), reported = 0.15
    is_consistent, diff = check_effect_size_consistency(sample_summary, 0.1575)
    assert is_consistent
    assert abs(diff - 0.05) < 1e-10

def test_check_effect_size_consistency_inconsistent(sample_summary):
    """Test effect size consistency when exceeding threshold"""
    # Reconstructed = 0.165 (10% higher than 0.15), reported = 0.15
    is_consistent, diff = check_effect_size_consistency(sample_summary, 0.165)
    assert not is_consistent
    assert abs(diff - 0.10) < 1e-10

def test_create_audit_record_consistent(sample_summary):
    """Test audit record creation for consistent summary"""
    record = create_audit_record(
        summary=sample_summary,
        is_p_consistent=True,
        p_difference=0.02,
        is_effect_consistent=True,
        effect_difference=0.03,
        has_sample_size_mismatch=False,
        reconstructed_p=0.05,
        reconstructed_effect=0.155
    )
    
    assert record.url == sample_summary.url
    assert not record.is_inconsistent
    assert record.warnings is None
    assert record.notes is None

def test_create_audit_record_p_inconsistent(sample_summary):
    """Test audit record creation for p-value inconsistency"""
    record = create_audit_record(
        summary=sample_summary,
        is_p_consistent=False,
        p_difference=0.07,
        is_effect_consistent=True,
        effect_difference=0.03,
        has_sample_size_mismatch=False,
        reconstructed_p=0.10,
        reconstructed_effect=0.155
    )
    
    assert record.is_inconsistent
    assert "P-value discrepancy" in record.notes
    assert record.warnings is None

def test_create_audit_record_sample_size_mismatch(sample_summary_mismatch):
    """Test audit record creation with sample size mismatch (FR-004b)"""
    record = create_audit_record(
        summary=sample_summary_mismatch,
        is_p_consistent=True,
        p_difference=0.01,
        is_effect_consistent=True,
        effect_difference=0.02,
        has_sample_size_mismatch=True,
        reconstructed_p=0.03,
        reconstructed_effect=0.12
    )
    
    assert not record.is_inconsistent  # Not inconsistent, but has warning
    assert record.warnings is not None
    assert "data_quality_warning" in record.warnings
    assert "excluded_from_prevalence" in record.warnings
    assert "Sample size mismatch" in record.notes

def test_validate_summary(sample_summary):
    """Test full validation of a summary"""
    record = validate_summary(
        summary=sample_summary,
        reconstructed_p=0.05,
        reconstructed_effect=0.155
    )
    
    assert record.url == sample_summary.url
    assert not record.is_inconsistent

def test_validate_summary_inconsistent(sample_summary):
    """Test validation with inconsistent values"""
    record = validate_summary(
        summary=sample_summary,
        reconstructed_p=0.10,  # Diff = 0.07 > 0.05
        reconstructed_effect=0.165  # Diff = 10% > 5%
    )
    
    assert record.is_inconsistent
    assert "P-value discrepancy" in record.notes
    assert "Effect size discrepancy" in record.notes

def test_validate_all_summaries():
    """Test validation of multiple summaries"""
    summaries = [
        ABTestSummary(
            url="test1.com", domain="test.com", publication_year=2023,
            outcome_type="binary", p_value=0.03, effect_size=0.10,
            sample_size_control=100, sample_size_treatment=100,
            total_sample_size=200, baseline_rate=0.1, treatment_rate=0.2
        ),
        ABTestSummary(
            url="test2.com", domain="test.com", publication_year=2023,
            outcome_type="binary", p_value=0.04, effect_size=0.12,
            sample_size_control=100, sample_size_treatment=100,
            total_sample_size=200, baseline_rate=0.1, treatment_rate=0.22
        )
    ]
    
    reconstructed = [
        {'p_value': 0.05, 'effect_size': 0.11},
        {'p_value': 0.10, 'effect_size': 0.13}  # Inconsistent
    ]
    
    records = validate_all_summaries(summaries, reconstructed)
    
    assert len(records) == 2
    assert not records[0].is_inconsistent
    assert records[1].is_inconsistent

def test_filter_for_prevalence_excludes_mismatch(sample_summary_mismatch):
    """Test that sample-size mismatch records are excluded from prevalence (FR-004b)"""
    consistent_record = create_audit_record(
        summary=sample_summary_mismatch,
        is_p_consistent=True,
        p_difference=0.01,
        is_effect_consistent=True,
        effect_difference=0.02,
        has_sample_size_mismatch=True,
        reconstructed_p=0.03,
        reconstructed_effect=0.12
    )
    
    clean_record = create_audit_record(
        summary=sample_summary_mismatch.model_copy(update={'total_sample_size': 1000}),
        is_p_consistent=True,
        p_difference=0.01,
        is_effect_consistent=True,
        effect_difference=0.02,
        has_sample_size_mismatch=False,
        reconstructed_p=0.03,
        reconstructed_effect=0.12
    )
    
    all_records = [consistent_record, clean_record]
    filtered = filter_for_prevalence(all_records)
    
    assert len(filtered) == 1
    assert filtered[0] == clean_record

def test_filter_for_prevalence_no_exclusions():
    """Test filtering when no records have mismatches"""
    record1 = create_audit_record(
        summary=ABTestSummary(
            url="test1", domain="test.com", publication_year=2023,
            outcome_type="binary", p_value=0.03, effect_size=0.10,
            sample_size_control=100, sample_size_treatment=100,
            total_sample_size=200, baseline_rate=0.1, treatment_rate=0.2
        ),
        is_p_consistent=True, p_difference=0.01,
        is_effect_consistent=True, effect_difference=0.02,
        has_sample_size_mismatch=False,
        reconstructed_p=0.04, reconstructed_effect=0.11
    )
    
    filtered = filter_for_prevalence([record1])
    assert len(filtered) == 1

def test_write_audit_report(tmp_path):
    """Test writing audit report to JSON file"""
    record = create_audit_record(
        summary=ABTestSummary(
            url="test.com", domain="test.com", publication_year=2023,
            outcome_type="binary", p_value=0.03, effect_size=0.10,
            sample_size_control=100, sample_size_treatment=100,
            total_sample_size=200, baseline_rate=0.1, treatment_rate=0.2
        ),
        is_p_consistent=False, p_difference=0.07,
        is_effect_consistent=True, effect_difference=0.02,
        has_sample_size_mismatch=False,
        reconstructed_p=0.10, reconstructed_effect=0.11
    )
    
    output_path = tmp_path / "audit_report.json"
    write_audit_report([record], output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]['url'] == "test.com"
    assert data[0]['is_inconsistent'] is True