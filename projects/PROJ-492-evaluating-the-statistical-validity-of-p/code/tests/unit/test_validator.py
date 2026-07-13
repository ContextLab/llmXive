"""
Unit tests for the Inconsistency Validator (T025).
Verifies FR-004 thresholds and FR-004b sample-size mismatch handling.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime

from code.src.audit.validator import (
    validate_single_summary,
    run_validator,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD
)
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger


@pytest.fixture
def consistent_summary():
    return ABTestSummary(
        source_url="http://test.com/consistent",
        domain="test.com",
        control_rate=0.10,
        treatment_rate=0.11,
        sample_size_control=1000,
        sample_size_treatment=1000,
        reported_p_value=0.04,
        reconstructed_p_value=0.039, # Diff < 0.05
        reconstructed_effect_size=0.10,
        reported_effect_size=0.10
    )


@pytest.fixture
def inconsistent_p_summary():
    return ABTestSummary(
        source_url="http://test.com/p-issue",
        domain="test.com",
        control_rate=0.10,
        treatment_rate=0.15,
        sample_size_control=1000,
        sample_size_treatment=1000,
        reported_p_value=0.01,
        reconstructed_p_value=0.07, # Diff = 0.06 > 0.05
        reconstructed_effect_size=0.50,
        reported_effect_size=0.50
    )


@pytest.fixture
def inconsistent_effect_summary():
    return ABTestSummary(
        source_url="http://test.com/effect-issue",
        domain="test.com",
        control_rate=0.10,
        treatment_rate=0.11,
        sample_size_control=1000,
        sample_size_treatment=1000,
        reported_p_value=0.04,
        reconstructed_p_value=0.04,
        reconstructed_effect_size=0.10,
        reported_effect_size=0.16 # Relative diff = |0.10 - 0.16|/0.10 = 0.6 > 0.05
    )


@pytest.fixture
def missing_baseline_summary():
    return ABTestSummary(
        source_url="http://test.com/missing-baseline",
        domain="test.com",
        control_rate=None,
        treatment_rate=0.11,
        sample_size_control=1000,
        sample_size_treatment=1000,
        reported_p_value=0.04,
        reconstructed_p_value=0.04,
        reconstructed_effect_size=None,
        reported_effect_size=None
    )


@pytest.fixture
def sample_size_zero_summary():
    return ABTestSummary(
        source_url="http://test.com/zero-sample",
        domain="test.com",
        control_rate=0.10,
        treatment_rate=0.11,
        sample_size_control=0,
        sample_size_treatment=1000,
        reported_p_value=0.04,
        reconstructed_p_value=0.04,
        reconstructed_effect_size=0.10,
        reported_effect_size=0.10
    )


def test_consistent_summary(consistent_summary):
    record = validate_single_summary(consistent_summary, get_default_logger())
    assert record.is_consistent is True
    assert record.issues is None or len(record.issues) == 0
    # Warnings might be empty or contain non-critical info, but not "inconsistent"
    assert record.data_quality_warning is False or (record.warnings and len(record.warnings) == 0)


def test_inconsistent_p_value(inconsistent_p_summary):
    record = validate_single_summary(inconsistent_p_summary, get_default_logger())
    assert record.is_consistent is False
    assert any("p-value" in issue.lower() for issue in record.issues)
    assert record.data_quality_warning is True


def test_inconsistent_effect_size(inconsistent_effect_summary):
    record = validate_single_summary(inconsistent_effect_summary, get_default_logger())
    assert record.is_consistent is False
    assert any("effect-size" in issue.lower() for issue in record.issues)
    assert record.data_quality_warning is True


def test_missing_baseline(missing_baseline_summary):
    record = validate_single_summary(missing_baseline_summary, get_default_logger())
    # Missing baseline should trigger a warning (FR-012)
    assert record.data_quality_warning is True
    assert any("missing baseline" in w.lower() for w in record.warnings)
    # Consistency might be True if no other issues, or False if missing data prevents check.
    # Based on implementation, it flags warning but might not mark inconsistent if no other data to contradict.
    # The task requires flagging in notes.
    assert "Missing baseline conversion rate" in record.warnings


def test_sample_size_zero(sample_size_zero_summary):
    record = validate_single_summary(sample_size_zero_summary, get_default_logger())
    assert record.data_quality_warning is True
    assert any("non-positive" in w.lower() for w in record.warnings)


def test_run_validator_batch(tmp_path):
    """Test the batch runner and file output."""
    summaries = [
        ABTestSummary(
            source_url="http://test.com/1",
            domain="test.com",
            control_rate=0.10,
            treatment_rate=0.11,
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.04,
            reconstructed_p_value=0.039,
            reconstructed_effect_size=0.10,
            reported_effect_size=0.10
        ),
        ABTestSummary(
            source_url="http://test.com/2",
            domain="test.com",
            control_rate=0.10,
            treatment_rate=0.15,
            sample_size_control=1000,
            sample_size_treatment=1000,
            reported_p_value=0.01,
            reconstructed_p_value=0.07,
            reconstructed_effect_size=0.50,
            reported_effect_size=0.50
        )
    ]
    
    output_file = tmp_path / "audit_report.json"
    records = run_validator(summaries, output_file)
    
    assert len(records) == 2
    assert records[0].is_consistent is True
    assert records[1].is_consistent is False
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[0]["is_consistent"] is True
    assert data[1]["is_consistent"] is False
    assert "issues" in data[1]
