"""
Unit tests for the inconsistency validator module.

Tests cover:
- Absolute p-difference > 0.05 threshold
- Relative effect-size > 5% threshold
- Inequality handling
- Sample-size mismatch detection and exclusion
- data_quality_warning generation
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

import numpy as np

from code.src.audit.validator import (
    check_sample_size_match,
    calculate_effect_size,
    calculate_effect_size_baseline,
    validate_p_value_consistency,
    validate_effect_size_consistency,
    validate_single_summary,
    validate_all_summaries,
    should_exclude_from_prevalence,
    write_audit_report,
    run_validator,
    ABSOLUTE_P_DIFF_THRESHOLD,
    RELATIVE_EFFECT_SIZE_THRESHOLD
)
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.config import SEED

# Set seed for reproducibility
np.random.seed(SEED)


@pytest.fixture
def valid_summary_binary():
    """Create a valid binary AB test summary."""
    return ABTestSummary(
        url="https://example.com/test1",
        domain="example.com",
        year=2024,
        is_binary=True,
        n_control=1000,
        n_treatment=1000,
        conversion_control=0.10,
        conversion_treatment=0.12,
        p_value_reported=0.03,
        reconstructed_p_value=0.03,
        reconstructed_effect_size=0.02,
        test_type="z-test"
    )


@pytest.fixture
def valid_summary_continuous():
    """Create a valid continuous AB test summary."""
    return ABTestSummary(
        url="https://example.com/test2",
        domain="example.com",
        year=2024,
        is_binary=False,
        n_control=500,
        n_treatment=500,
        mean_control=10.0,
        mean_treatment=11.0,
        std_control=2.0,
        std_treatment=2.0,
        reconstructed_p_value=0.01,
        reconstructed_effect_size=1.0,
        test_type="t-test"
    )


@pytest.fixture
def summary_with_sample_size_mismatch():
    """Create a summary with extreme sample size mismatch."""
    return ABTestSummary(
        url="https://example.com/test3",
        domain="example.com",
        year=2024,
        is_binary=True,
        n_control=100,
        n_treatment=10000,  # 100x mismatch
        conversion_control=0.10,
        conversion_treatment=0.12,
        reconstructed_p_value=0.05,
        reconstructed_effect_size=0.02,
        test_type="z-test"
    )


@pytest.fixture
def summary_with_p_value_inconsistency():
    """Create a summary with p-value inconsistency."""
    return ABTestSummary(
        url="https://example.com/test4",
        domain="example.com",
        year=2024,
        is_binary=True,
        n_control=1000,
        n_treatment=1000,
        conversion_control=0.10,
        conversion_treatment=0.12,
        reconstructed_p_value=0.15,  # High reported
        reconstructed_effect_size=0.02,
        test_type="z-test"
    )


@pytest.fixture
def summary_with_effect_size_inconsistency():
    """Create a summary with effect size inconsistency."""
    return ABTestSummary(
        url="https://example.com/test5",
        domain="example.com",
        year=2024,
        is_binary=True,
        n_control=1000,
        n_treatment=1000,
        conversion_control=0.10,
        conversion_treatment=0.12,
        reconstructed_p_value=0.03,
        reconstructed_effect_size=0.10,  # Large reported effect
        test_type="z-test"
    )


def test_check_sample_size_match_valid():
    """Test that valid sample sizes pass the check."""
    summary = ABTestSummary(
        url="https://example.com",
        domain="example.com",
        year=2024,
        is_binary=True,
        n_control=1000,
        n_treatment=1000,
        conversion_control=0.10,
        conversion_treatment=0.12
    )
    
    is_match, error = check_sample_size_match(summary)
    assert is_match is True
    assert error is None


def test_check_sample_size_match_missing():
    """Test that missing sample sizes fail the check."""
    summary = ABTestSummary(
        url="https://example.com",
        domain="example.com",
        year=2024,
        is_binary=True,
        n_control=None,
        n_treatment=1000,
        conversion_control=0.10,
        conversion_treatment=0.12
    )
    
    is_match, error = check_sample_size_match(summary)
    assert is_match is False
    assert "Missing sample size data" in error


def test_check_sample_size_match_invalid_values():
    """Test that invalid sample sizes (<=0) fail the check."""
    summary = ABTestSummary(
        url="https://example.com",
        domain="example.com",
        year=2024,
        is_binary=True,
        n_control=0,
        n_treatment=1000,
        conversion_control=0.10,
        conversion_treatment=0.12
    )
    
    is_match, error = check_sample_size_match(summary)
    assert is_match is False
    assert "Invalid sample size" in error


def test_check_sample_size_match_extreme_mismatch():
    """Test that extreme sample size mismatches are detected."""
    summary = ABTestSummary(
        url="https://example.com",
        domain="example.com",
        year=2024,
        is_binary=True,
        n_control=100,
        n_treatment=10000,  # 100x ratio
        conversion_control=0.10,
        conversion_treatment=0.12
    )
    
    is_match, error = check_sample_size_match(summary)
    assert is_match is False
    assert "Extreme sample size mismatch" in error


def test_calculate_effect_size_binary():
    """Test effect size calculation for binary outcomes."""
    summary = ABTestSummary(
        url="https://example.com",
        domain="example.com",
        year=2024,
        is_binary=True,
        n_control=1000,
        n_treatment=1000,
        conversion_control=0.10,
        conversion_treatment=0.12
    )
    
    effect_size = calculate_effect_size(summary)
    assert effect_size == 0.02


def test_calculate_effect_size_continuous():
    """Test effect size calculation for continuous outcomes."""
    summary = ABTestSummary(
        url="https://example.com",
        domain="example.com",
        year=2024,
        is_binary=False,
        n_control=1000,
        n_treatment=1000,
        mean_control=10.0,
        mean_treatment=11.5
    )
    
    effect_size = calculate_effect_size(summary)
    assert effect_size == 1.5


def test_calculate_effect_size_missing():
    """Test effect size calculation with missing data."""
    summary = ABTestSummary(
        url="https://example.com",
        domain="example.com",
        year=2024,
        is_binary=True,
        n_control=1000,
        n_treatment=1000,
        conversion_control=None,
        conversion_treatment=0.12
    )
    
    effect_size = calculate_effect_size(summary)
    assert effect_size is None


def test_validate_p_value_consistency_consistent():
    """Test p-value validation with consistent values."""
    is_consistent, error = validate_p_value_consistency(0.03, 0.035)
    assert is_consistent is True
    assert error is None


def test_validate_p_value_consistency_inconsistent():
    """Test p-value validation with inconsistent values (diff > 0.05)."""
    is_consistent, error = validate_p_value_consistency(0.03, 0.10)
    assert is_consistent is False
    assert error is not None
    assert "P-value discrepancy" in error


def test_validate_p_value_consistency_missing():
    """Test p-value validation with missing values."""
    is_consistent, error = validate_p_value_consistency(None, 0.03)
    assert is_consistent is True
    assert error is None


def test_validate_effect_size_consistency_consistent():
    """Test effect size validation with consistent values."""
    is_consistent, error = validate_effect_size_consistency(0.02, 0.021, 0.10)
    assert is_consistent is True
    assert error is None


def test_validate_effect_size_consistency_inconsistent():
    """Test effect size validation with inconsistent values (relative diff > 5%)."""
    # Relative diff = |0.02 - 0.03| / 0.10 = 0.10 = 10% > 5%
    is_consistent, error = validate_effect_size_consistency(0.02, 0.03, 0.10)
    assert is_consistent is False
    assert error is not None
    assert "Effect size discrepancy" in error


def test_validate_effect_size_consistency_zero_baseline():
    """Test effect size validation with zero baseline."""
    # Should fall back to absolute comparison
    is_consistent, error = validate_effect_size_consistency(0.02, 0.021, 0.0)
    assert is_consistent is True
    assert error is None


def test_validate_single_summary_no_issues(valid_summary_binary):
    """Test validation of a summary with no issues."""
    reconstructed_p = 0.03
    reconstructed_effect = 0.02
    
    record = validate_single_summary(valid_summary_binary, reconstructed_p, reconstructed_effect)
    
    assert record.is_inconsistent is False
    assert record.sample_size_warning is None
    assert len(record.warnings) == 0
    assert len(record.inconsistencies) == 0


def test_validate_single_summary_p_value_issue(summary_with_p_value_inconsistency):
    """Test validation of a summary with p-value inconsistency."""
    # Reconstructed p is 0.03, reported is 0.15 -> diff = 0.12 > 0.05
    reconstructed_p = 0.03
    reconstructed_effect = 0.02
    
    record = validate_single_summary(summary_with_p_value_inconsistency, reconstructed_p, reconstructed_effect)
    
    assert record.is_inconsistent is True
    assert len(record.inconsistencies) == 1
    assert record.inconsistencies[0]["type"] == "p_value_inconsistency"


def test_validate_single_summary_effect_size_issue(summary_with_effect_size_inconsistency):
    """Test validation of a summary with effect size inconsistency."""
    reconstructed_p = 0.03
    reconstructed_effect = 0.02  # Reconstructed is 0.02, reported is 0.10
    
    record = validate_single_summary(summary_with_effect_size_inconsistency, reconstructed_p, reconstructed_effect)
    
    assert record.is_inconsistent is True
    assert len(record.inconsistencies) == 1
    assert record.inconsistencies[0]["type"] == "effect_size_inconsistency"


def test_validate_single_summary_sample_size_warning(summary_with_sample_size_mismatch):
    """Test validation of a summary with sample size mismatch."""
    reconstructed_p = 0.03
    reconstructed_effect = 0.02
    
    record = validate_single_summary(summary_with_sample_size_mismatch, reconstructed_p, reconstructed_effect)
    
    assert record.sample_size_warning is not None
    assert record.data_quality_warning is True
    assert len(record.warnings) == 1
    assert record.warnings[0]["code"] == "ERR-101"


def test_should_exclude_from_prevalence_no_warning(valid_summary_binary):
    """Test that records without warnings are included in prevalence."""
    record = validate_single_summary(valid_summary_binary, 0.03, 0.02)
    assert should_exclude_from_prevalence(record) is False


def test_should_exclude_from_prevalence_with_warning(summary_with_sample_size_mismatch):
    """Test that records with sample size warnings are excluded from prevalence."""
    record = validate_single_summary(summary_with_sample_size_mismatch, 0.03, 0.02)
    assert should_exclude_from_prevalence(record) is True


def test_validate_all_summaries(tmp_path):
    """Test validation of multiple summaries."""
    summaries = [
        ABTestSummary(
            url="https://example.com/1",
            domain="example.com",
            year=2024,
            is_binary=True,
            n_control=1000,
            n_treatment=1000,
            conversion_control=0.10,
            conversion_treatment=0.12,
            reconstructed_p_value=0.03,
            reconstructed_effect_size=0.02
        ),
        ABTestSummary(
            url="https://example.com/2",
            domain="example.com",
            year=2024,
            is_binary=True,
            n_control=100,
            n_treatment=10000,  # Mismatch
            conversion_control=0.10,
            conversion_treatment=0.12,
            reconstructed_p_value=0.03,
            reconstructed_effect_size=0.02
        ),
        ABTestSummary(
            url="https://example.com/3",
            domain="example.com",
            year=2024,
            is_binary=True,
            n_control=1000,
            n_treatment=1000,
            conversion_control=0.10,
            conversion_treatment=0.12,
            reconstructed_p_value=0.15,  # Inconsistent p-value
            reconstructed_effect_size=0.02
        )
    ]
    
    reconstructed_results = {
        "https://example.com/1": {"p_value": 0.03, "effect_size": 0.02},
        "https://example.com/2": {"p_value": 0.03, "effect_size": 0.02},
        "https://example.com/3": {"p_value": 0.03, "effect_size": 0.02}
    }
    
    records = validate_all_summaries(summaries, reconstructed_results)
    
    assert len(records) == 3
    
    # First record: no issues
    assert records[0].is_inconsistent is False
    assert records[0].sample_size_warning is None
    
    # Second record: sample size warning
    assert records[1].sample_size_warning is not None
    assert records[1].data_quality_warning is True
    
    # Third record: p-value inconsistency
    assert records[2].is_inconsistent is True
    assert len(records[2].inconsistencies) == 1


def test_write_audit_report(tmp_path):
    """Test writing audit report to JSON file."""
    summaries = [
        ABTestSummary(
            url="https://example.com/1",
            domain="example.com",
            year=2024,
            is_binary=True,
            n_control=1000,
            n_treatment=1000,
            conversion_control=0.10,
            conversion_treatment=0.12,
            reconstructed_p_value=0.03,
            reconstructed_effect_size=0.02
        ),
        ABTestSummary(
            url="https://example.com/2",
            domain="example.com",
            year=2024,
            is_binary=True,
            n_control=100,
            n_treatment=10000,
            conversion_control=0.10,
            conversion_treatment=0.12,
            reconstructed_p_value=0.03,
            reconstructed_effect_size=0.02
        )
    ]
    
    reconstructed_results = {
        "https://example.com/1": {"p_value": 0.03, "effect_size": 0.02},
        "https://example.com/2": {"p_value": 0.03, "effect_size": 0.02}
    }
    
    output_path = tmp_path / "audit_report.json"
    
    audit_records = validate_all_summaries(summaries, reconstructed_results)
    summary = write_audit_report(audit_records, output_path)
    
    assert output_path.exists()
    
    # Verify summary statistics
    assert summary["total_summaries"] == 2
    assert summary["sample_size_warning_count"] == 1
    assert summary["valid_for_prevalence_count"] == 1  # Excludes the one with warning
    
    # Verify JSON content
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert "summary" in report
    assert "records" in report
    assert len(report["records"]) == 2


def test_run_validator_integration(tmp_path):
    """Test the full validation pipeline."""
    summaries = [
        ABTestSummary(
            url="https://example.com/1",
            domain="example.com",
            year=2024,
            is_binary=True,
            n_control=1000,
            n_treatment=1000,
            conversion_control=0.10,
            conversion_treatment=0.12,
            reconstructed_p_value=0.03,
            reconstructed_effect_size=0.02
        )
    ]
    
    reconstructed_results = {
        "https://example.com/1": {"p_value": 0.03, "effect_size": 0.02}
    }
    
    output_path = tmp_path / "audit_report.json"
    
    summary = run_validator(summaries, reconstructed_results, output_path)
    
    assert output_path.exists()
    assert summary["total_summaries"] == 1
    assert summary["inconsistent_count"] == 0
    assert summary["prevalence_rate_excluding_warnings"] == 0.0
