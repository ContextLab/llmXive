"""
Unit tests for the Inconsistency Validator (T025).

Covers:
- Absolute p-difference > 0.05
- Relative effect-size > 5%
- Inequality handling
- Sample-size mismatch generation of data_quality_warning
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
from code.src.models.data_models import ABTestSummary
from code.src.audit.validator import (
    run_validator,
    calculate_relative_difference,
    validate_single_summary,
    THRESHOLD_P_ABSOLUTE,
    THRESHOLD_EFFECT_RELATIVE
)


def test_calculate_relative_difference():
    """Test relative difference calculation."""
    assert calculate_relative_difference(10, 10) == 0.0
    assert calculate_relative_difference(10, 0) == 1.0
    assert calculate_relative_difference(0, 10) == 1.0
    assert abs(calculate_relative_difference(100, 105) - 0.05) < 1e-6


def test_validate_single_summary_p_value_mismatch():
    """Test detection of p-value mismatch > 0.05."""
    summary = ABTestSummary(
        id="test-1",
        url="http://example.com",
        domain="example.com",
        p_value=0.01,
        effect_size=0.5,
        sample_size=1000
    )
    # Reconstructed p-value is far off
    is_consistent, p_reason, effect_reason, has_n_warning = validate_single_summary(
        summary, reconstructed_p_value=0.10, reconstructed_effect_size=0.5
    )
    assert not is_consistent
    assert p_reason is not None
    assert "P-value discrepancy" in p_reason
    assert effect_reason is None
    assert not has_n_warning


def test_validate_single_summary_effect_size_mismatch():
    """Test detection of effect-size mismatch > 5%."""
    summary = ABTestSummary(
        id="test-2",
        url="http://example.com",
        domain="example.com",
        p_value=0.03,
        effect_size=1.0,
        sample_size=1000
    )
    # Reconstructed effect size is 10% different (0.9 vs 1.0 -> 10% diff)
    is_consistent, p_reason, effect_reason, has_n_warning = validate_single_summary(
        summary, reconstructed_p_value=0.03, reconstructed_effect_size=0.9
    )
    assert not is_consistent
    assert effect_reason is not None
    assert "Effect size discrepancy" in effect_reason
    assert p_reason is None
    assert not has_n_warning


def test_validate_single_summary_sample_size_mismatch():
    """Test detection of sample size mismatch and warning generation."""
    summary = ABTestSummary(
        id="test-3",
        url="http://example.com",
        domain="example.com",
        p_value=0.03,
        effect_size=0.5,
        sample_size=1000
    )
    # Reconstructed sample size is different
    is_consistent, p_reason, effect_reason, has_n_warning = validate_single_summary(
        summary, 
        reconstructed_p_value=0.03, 
        reconstructed_effect_size=0.5,
        reconstructed_sample_size=900
    )
    # Statistical values are consistent, but sample size is not
    # The function returns is_consistent=True for stats, but has_n_warning=True
    assert is_consistent # Stats are fine
    assert has_n_warning
    assert p_reason is None
    assert effect_reason is None


def test_run_validator_integration():
    """Test the full run_validator function and output generation."""
    summaries = [
        ABTestSummary(
            id="s1",
            url="http://a.com",
            domain="a.com",
            p_value=0.01,
            effect_size=0.5,
            sample_size=1000
        ),
        ABTestSummary(
            id="s2",
            url="http://b.com",
            domain="b.com",
            p_value=0.03,
            effect_size=1.0,
            sample_size=2000
        )
    ]

    reconstructed_results = [
        {
            "summary_id": "s1",
            "p_value": 0.10, # Mismatch
            "effect_size": 0.5,
            "sample_size": 1000
        },
        {
            "summary_id": "s2",
            "p_value": 0.03,
            "effect_size": 1.0,
            "sample_size": 1800 # Mismatch
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "audit_report.json"
        records = run_validator(summaries, reconstructed_results, output_path)

        assert len(records) == 2
        
        # Check first record (p-value mismatch)
        r1 = records[0]
        assert "p_value_mismatch" in r1.flags
        assert not r1.exclude_from_prevalence
        
        # Check second record (sample size mismatch)
        r2 = records[1]
        assert "sample_size_mismatch" in r2.flags
        assert r2.exclude_from_prevalence
        assert "data_quality_warning" in r2.notes

        # Verify file exists and is valid JSON
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 2
            assert data[0]['flags'] == ["p_value_mismatch"]
            assert data[1]['flags'] == ["sample_size_mismatch"]
            assert data[1]['exclude_from_prevalence'] is True
