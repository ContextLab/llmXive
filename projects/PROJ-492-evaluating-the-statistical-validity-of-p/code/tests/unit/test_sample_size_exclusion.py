"""
Test for FR-004b: Sample-size mismatch entries excluded from aggregate prevalence.

This test verifies that records flagged with data_quality_warning due to
sample-size discrepancies are excluded from prevalence calculations.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from code.src.audit.validator import (
    validate_all_summaries,
    get_inconsistency_prevalence,
    run_validator
)
from code.src.models.data_models import ABTestSummary


def test_sample_size_exclusion_from_prevalence(tmp_path):
    """
    Verify that sample-size mismatch entries are excluded from aggregate 
    prevalence estimates per FR-004b.
    """
    # Create test summaries with various conditions
    summaries = [
        # Consistent record (should be counted)
        ABTestSummary(
            url="https://test1.com",
            domain="test.com",
            year=2023,
            baseline_rate=0.10,
            treatment_rate=0.12,
            n_control=1000,
            n_treatment=1000,
            reported_p_value=0.03,
            reconstructed_p_value=0.04,
            reported_effect_size=0.02,
            reconstructed_effect_size=0.021,
            test_type="binary",
            is_significant=True
        ),
        # Inconsistent record but valid sample size (should be counted as inconsistent)
        ABTestSummary(
            url="https://test2.com",
            domain="test.com",
            year=2023,
            baseline_rate=0.10,
            treatment_rate=0.15,
            n_control=1000,
            n_treatment=1000,
            reported_p_value=0.01,
            reconstructed_p_value=0.12,  # Large difference
            reported_effect_size=0.05,
            reconstructed_effect_size=0.051,
            test_type="binary",
            is_significant=True
        ),
        # Sample size mismatch (should be EXCLUDED from prevalence)
        ABTestSummary(
            url="https://test3.com",
            domain="test.com",
            year=2023,
            baseline_rate=0.10,
            treatment_rate=0.12,
            n_control=1000,
            n_treatment=None,  # Missing sample size
            reported_p_value=0.03,
            reconstructed_p_value=0.04,
            reported_effect_size=0.02,
            reconstructed_effect_size=0.021,
            test_type="binary",
            is_significant=True
        ),
        # Another sample size mismatch (should be EXCLUDED)
        ABTestSummary(
            url="https://test4.com",
            domain="test.com",
            year=2023,
            baseline_rate=0.10,
            treatment_rate=0.12,
            n_control=0,  # Invalid sample size
            n_treatment=1000,
            reported_p_value=0.03,
            reconstructed_p_value=0.04,
            reported_effect_size=0.02,
            reconstructed_effect_size=0.021,
            test_type="binary",
            is_significant=True
        )
    ]
    
    # Validate all summaries
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    
    with open(input_path, 'w') as f:
        json.dump([s.__dict__ for s in summaries], f)
    
    result = run_validator(input_path, output_path, exclude_quality_warnings=True)
    
    stats = result["prevalence_statistics"]
    
    # Total records
    assert stats["total_records"] == 4
    
    # Two records should be excluded due to sample-size mismatches
    assert stats["excluded_count"] == 2
    
    # Only 2 records should be valid for prevalence calculation
    assert stats["valid_records"] == 2
    
    # Among valid records: 1 consistent, 1 inconsistent
    assert stats["inconsistent_count"] == 1
    
    # Prevalence should be 50% (1 out of 2 valid records)
    assert abs(stats["inconsistent_rate"] - 0.5) < 0.001
    
    # Verify exclusion policy is recorded
    assert stats["exclusion_policy"] == "sample_size_mismatch"


def test_sample_size_warning_flagged_in_audit_record(tmp_path):
    """
    Verify that records with sample-size mismatches are flagged with
    data_quality_warning in the AuditRecord.
    """
    summaries = [
        ABTestSummary(
            url="https://test1.com",
            domain="test.com",
            year=2023,
            baseline_rate=0.10,
            treatment_rate=0.12,
            n_control=1000,
            n_treatment=None,  # Missing
            reported_p_value=0.03,
            reconstructed_p_value=0.04,
            reported_effect_size=0.02,
            reconstructed_effect_size=0.021,
            test_type="binary",
            is_significant=True
        )
    ]
    
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    
    with open(input_path, 'w') as f:
        json.dump([s.__dict__ for s in summaries], f)
    
    run_validator(input_path, output_path)
    
    # Load and verify output
    with open(output_path, 'r') as f:
        records = json.load(f)
    
    assert len(records) == 1
    assert records[0]["data_quality_warning"] is True
    assert records[0]["sample_size_mismatch"] is True
    assert "Sample size issue" in records[0]["notes"]


def test_prevalence_without_exclusion_includes_all(tmp_path):
    """
    Verify that when exclude_quality_warnings=False, all records are included.
    """
    summaries = [
        ABTestSummary(
            url="https://test1.com",
            domain="test.com",
            year=2023,
            baseline_rate=0.10,
            treatment_rate=0.12,
            n_control=1000,
            n_treatment=1000,
            reported_p_value=0.03,
            reconstructed_p_value=0.04,
            reported_effect_size=0.02,
            reconstructed_effect_size=0.021,
            test_type="binary",
            is_significant=True
        ),
        ABTestSummary(
            url="https://test2.com",
            domain="test.com",
            year=2023,
            baseline_rate=0.10,
            treatment_rate=0.12,
            n_control=1000,
            n_treatment=None,
            reported_p_value=0.03,
            reconstructed_p_value=0.04,
            reported_effect_size=0.02,
            reconstructed_effect_size=0.021,
            test_type="binary",
            is_significant=True
        )
    ]
    
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "output.json"
    
    with open(input_path, 'w') as f:
        json.dump([s.__dict__ for s in summaries], f)
    
    # Run with exclusion disabled
    result = run_validator(input_path, output_path, exclude_quality_warnings=False)
    
    stats = result["prevalence_statistics"]
    
    assert stats["total_records"] == 2
    assert stats["excluded_count"] == 0
    assert stats["valid_records"] == 2
    assert stats["inconsistent_count"] == 1  # One has sample-size issue, counted as inconsistent
    assert stats["inconsistent_rate"] == 0.5