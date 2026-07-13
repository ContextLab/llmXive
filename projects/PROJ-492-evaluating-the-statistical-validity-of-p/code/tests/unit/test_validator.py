"""
Unit tests for the Inconsistency Validator (T025).
"""
import pytest
import json
from pathlib import Path
from code.src.audit.validator import (
    validate_single_summary,
    calculate_relative_difference,
    run_validator,
    write_audit_report
)
from code.src.models.data_models import ABTestSummary

def test_calculate_relative_difference_basic():
    assert calculate_relative_difference(10.0, 10.0) == 0.0
    assert calculate_relative_difference(10.0, 11.0) == 1.0 / 11.0
    assert calculate_relative_difference(0.0, 0.0) == 0.0
    assert calculate_relative_difference(0.0, 1.0) == 1.0
    assert calculate_relative_difference(1.0, 0.0) == 1.0

def test_calculate_relative_difference_none():
    assert calculate_relative_difference(None, 1.0) is None
    assert calculate_relative_difference(1.0, None) is None

def test_validate_p_value_consistency():
    # Create a summary with a reported p-value
    summary = ABTestSummary(
        url="http://example.com/test1",
        domain="example.com",
        year=2023,
        n_control=1000,
        n_treatment=1000,
        control_rate=0.1,
        treatment_rate=0.12,
        p_value=0.04,
        effect_size=0.02
    )
    
    # Case 1: Reconstructed p-value is close (consistent)
    rec_close = {'p_value': 0.041, 'effect_size': 0.02, 'n_control': 1000, 'n_treatment': 1000}
    is_consistent, warnings, mismatch = validate_single_summary(summary, rec_close)
    assert is_consistent is True
    assert len(warnings) == 0
    assert mismatch is False

    # Case 2: Reconstructed p-value is far (inconsistent)
    rec_far = {'p_value': 0.15, 'effect_size': 0.02, 'n_control': 1000, 'n_treatment': 1000}
    is_consistent, warnings, mismatch = validate_single_summary(summary, rec_far)
    assert is_consistent is False
    assert any("P-value inconsistency" in w for w in warnings)
    assert mismatch is False

def test_validate_effect_size_consistency():
    summary = ABTestSummary(
        url="http://example.com/test2",
        domain="example.com",
        year=2023,
        n_control=1000,
        n_treatment=1000,
        control_rate=0.1,
        treatment_rate=0.12,
        p_value=0.04,
        effect_size=0.02
    )
    
    # Case 1: Effect size close
    rec_close = {'p_value': 0.04, 'effect_size': 0.021, 'n_control': 1000, 'n_treatment': 1000}
    is_consistent, warnings, mismatch = validate_single_summary(summary, rec_close)
    assert is_consistent is True
    
    # Case 2: Effect size far (> 5% relative diff)
    # 0.02 vs 0.03 -> diff 0.01, max 0.03 -> 0.33 > 0.05
    rec_far = {'p_value': 0.04, 'effect_size': 0.03, 'n_control': 1000, 'n_treatment': 1000}
    is_consistent, warnings, mismatch = validate_single_summary(summary, rec_far)
    assert is_consistent is False
    assert any("Effect size inconsistency" in w for w in warnings)

def test_validate_sample_size_mismatch():
    summary = ABTestSummary(
        url="http://example.com/test3",
        domain="example.com",
        year=2023,
        n_control=1000,
        n_treatment=1000,
        control_rate=0.1,
        treatment_rate=0.12,
        p_value=0.04,
        effect_size=0.02
    )
    
    # Case: Sample size mismatch
    rec_mismatch = {'p_value': 0.04, 'effect_size': 0.02, 'n_control': 1000, 'n_treatment': 500}
    is_consistent, warnings, mismatch = validate_single_summary(summary, rec_mismatch)
    
    assert is_consistent is False
    assert mismatch is True
    assert any("Sample size mismatch" in w for w in warnings)

def test_run_validator_integration(tmp_path):
    # Prepare test data
    summaries = [
        ABTestSummary(
            url="http://a.com", domain="a.com", year=2023,
            n_control=1000, n_treatment=1000,
            control_rate=0.1, treatment_rate=0.12,
            p_value=0.04, effect_size=0.02
        ),
        ABTestSummary(
            url="http://b.com", domain="b.com", year=2023,
            n_control=1000, n_treatment=1000,
            control_rate=0.1, treatment_rate=0.12,
            p_value=0.04, effect_size=0.02
        )
    ]
    
    reconstructed = [
        {'p_value': 0.041, 'effect_size': 0.02, 'n_control': 1000, 'n_treatment': 1000}, # Consistent
        {'p_value': 0.15, 'effect_size': 0.02, 'n_control': 1000, 'n_treatment': 1000}  # Inconsistent
    ]
    
    records = run_validator(summaries, reconstructed)
    
    assert len(records) == 2
    assert records[0].is_consistent is True
    assert records[1].is_consistent is False
    assert records[1].data_quality_warning is not None

    # Test writing
    output_path = tmp_path / "audit_report.json"
    write_audit_report(records, str(output_path))
    
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]['is_consistent'] is True
    assert data[1]['is_consistent'] is False
    assert 'Sample size mismatch' not in str(data[1].get('warnings', [])) # Only p-value issue here
    assert 'P-value inconsistency' in str(data[1].get('warnings', []))
