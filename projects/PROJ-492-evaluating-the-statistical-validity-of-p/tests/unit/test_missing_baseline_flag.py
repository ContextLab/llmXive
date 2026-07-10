"""
Test for T025b: Verify that entries with missing baseline conversion rates
are flagged in the audit notes as required by FR-012.
"""
import json
import pytest
from pathlib import Path
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.reconstructor import reconstruct_single_summary
from code.src.audit.validator import validate_single_record, validate_all_records
from code.src.utils.logger import get_default_logger, get_error_message
from code.src.config import SEED

import numpy as np

# Ensure deterministic behavior for tests
np.random.seed(SEED)

def test_missing_baseline_flag_in_audit_notes():
    """
    Verify that if a summary has a missing baseline conversion rate,
    the resulting AuditRecord contains a flag in the notes indicating
    this missing data, per FR-012.
    """
    # Create a synthetic summary with missing baseline conversion rate
    # but with other required fields to allow partial reconstruction
    summary = ABTestSummary(
        url="https://example.com/test1",
        domain="example.com",
        sample_size_control=1000,
        sample_size_treatment=1000,
        conversion_rate_control=None,  # Missing baseline
        conversion_rate_treatment=0.05,
        p_value_reported=0.03,
        effect_size_reported=0.02,
        test_type="binary",
        publication_year=2023
    )

    # Reconstruct statistical values
    reconstructed = reconstruct_single_summary(summary)

    # Validate the record
    # The validator should detect the missing baseline and flag it
    audit_record = validate_single_record(summary, reconstructed)

    # Assert that the audit record was created
    assert audit_record is not None, "Audit record should be created even with missing data"

    # Check that the notes field contains a flag about the missing baseline
    # per FR-012 requirement
    notes = audit_record.notes if audit_record.notes else ""
    assert "missing baseline" in notes.lower() or "baseline conversion rate missing" in notes.lower(), (
        f"Audit record notes should flag missing baseline conversion rate. "
        f"Current notes: '{notes}'"
    )

    # Also verify that a data_quality_warning is present
    assert audit_record.data_quality_warning is not None, (
        "Data quality warning should be present for missing baseline"
    )

def test_present_baseline_no_flag():
    """
    Verify that when baseline conversion rate is present, no missing baseline
    flag appears in the audit notes.
    """
    summary = ABTestSummary(
        url="https://example.com/test2",
        domain="example.com",
        sample_size_control=1000,
        sample_size_treatment=1000,
        conversion_rate_control=0.05,  # Present baseline
        conversion_rate_treatment=0.07,
        p_value_reported=0.03,
        effect_size_reported=0.02,
        test_type="binary",
        publication_year=2023
    )

    reconstructed = reconstruct_single_summary(summary)
    audit_record = validate_single_record(summary, reconstructed)

    notes = audit_record.notes if audit_record.notes else ""
    # Should not contain missing baseline flag
    assert "missing baseline" not in notes.lower(), (
        f"Audit record notes should NOT flag missing baseline when data is present. "
        f"Current notes: '{notes}'"
    )

def test_missing_baseline_in_batch_validation():
    """
    Test that batch validation correctly flags multiple records with missing baselines.
    """
    summaries = [
        ABTestSummary(
            url=f"https://example.com/test{i}",
            domain="example.com",
            sample_size_control=1000,
            sample_size_treatment=1000,
            conversion_rate_control=None if i % 2 == 0 else 0.05,
            conversion_rate_treatment=0.05,
            p_value_reported=0.03,
            effect_size_reported=0.02,
            test_type="binary",
            publication_year=2023
        )
        for i in range(10)
    ]

    reconstructed_list = [reconstruct_single_summary(s) for s in summaries]
    audit_records = validate_all_records(summaries, reconstructed_list)

    # Count records with missing baseline flags
    missing_baseline_count = 0
    for record in audit_records:
        notes = record.notes if record.notes else ""
        if "missing baseline" in notes.lower():
            missing_baseline_count += 1
            assert record.data_quality_warning is not None

    # Expected: 5 records (indices 0, 2, 4, 6, 8) have missing baseline
    assert missing_baseline_count == 5, (
        f"Expected 5 records with missing baseline flags, got {missing_baseline_count}"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
