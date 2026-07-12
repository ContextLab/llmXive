"""
Unit tests for the validator module (T025).
Covers:
- Absolute p-difference > 0.05 flagging
- Relative effect-size > 5% flagging
- Inequality p-value handling (flagging when reported p is 'p < 0.05' etc.)
- Sample-size mismatch detection with data_quality_warning generation
"""

import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

# Ensure project root is on path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from code.src.audit.validator import (
    check_p_value_consistency,
    check_effect_size_consistency,
    handle_inequality_p_value,
    check_sample_size_consistency,
    validate_single_record,
    run_validation,
    main,
)
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.utils.logger import get_default_logger, AuditLogger


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def logger_fixture():
    """Provide a logger instance for tests."""
    return get_default_logger()


@pytest.fixture
def binary_summary_consistent() -> ABTestSummary:
    """
    A binary outcome summary that is internally consistent:
    - Baseline: 1000, 100 events -> p_b = 0.10
    - Variant: 1000, 150 events -> p_v = 0.15
    - Reported p-value: 0.001 (z-test approximation)
    - Effect size (absolute difference): 0.05 (5%)
    """
    return ABTestSummary(
        url="https://example.com/test1",
        test_type="binary",
        baseline_n=1000,
        baseline_events=100,
        variant_n=1000,
        variant_events=150,
        reported_p_value=0.001,
        reported_effect_size=0.05,
        reported_effect_size_type="absolute",
        baseline_rate=0.10,
        variant_rate=0.15,
    )


@pytest.fixture
def binary_summary_p_mismatch() -> ABTestSummary:
    """
    Same as binary_summary_consistent but with a reported p-value that
    differs significantly from the reconstructed one (> 0.05 absolute diff).
    """
    return ABTestSummary(
        url="https://example.com/test2",
        test_type="binary",
        baseline_n=1000,
        baseline_events=100,
        variant_n=1000,
        variant_events=150,
        reported_p_value=0.200,  # Large mismatch vs reconstructed ~0.001
        reported_effect_size=0.05,
        reported_effect_size_type="absolute",
        baseline_rate=0.10,
        variant_rate=0.15,
    )


@pytest.fixture
def binary_summary_effect_size_mismatch() -> ABTestSummary:
    """
    Same as binary_summary_consistent but with a reported effect size
    that differs significantly from the reconstructed one (> 5% relative diff).
    """
    return ABTestSummary(
        url="https://example.com/test3",
        test_type="binary",
        baseline_n=1000,
        baseline_events=100,
        variant_n=1000,
        variant_events=150,
        reported_p_value=0.001,
        reported_effect_size=0.08,  # 60% relative diff from 0.05
        reported_effect_size_type="absolute",
        baseline_rate=0.10,
        variant_rate=0.15,
    )


@pytest.fixture
def binary_summary_inequality_p() -> ABTestSummary:
    """
    A binary summary where the reported p-value is an inequality (e.g. 'p < 0.05').
    """
    return ABTestSummary(
        url="https://example.com/test4",
        test_type="binary",
        baseline_n=1000,
        baseline_events=100,
        variant_n=1000,
        variant_events=150,
        reported_p_value="p < 0.05",
        reported_effect_size=0.05,
        reported_effect_size_type="absolute",
        baseline_rate=0.10,
        variant_rate=0.15,
    )


@pytest.fixture
def binary_summary_sample_size_mismatch() -> ABTestSummary:
    """
    A binary summary where the reported sample sizes in the summary fields
    do not match the computed totals from events/rates (simulating a data
    quality issue).
    """
    return ABTestSummary(
        url="https://example.com/test5",
        test_type="binary",
        baseline_n=1000,
        baseline_events=100,
        variant_n=1000,
        variant_events=150,
        reported_p_value=0.001,
        reported_effect_size=0.05,
        reported_effect_size_type="absolute",
        baseline_rate=0.10,
        variant_rate=0.15,
        # Intentionally set a mismatched field if the model allows,
        # or we simulate by passing inconsistent data to the validator
        # that expects consistency.
        # Note: The ABTestSummary model may enforce consistency via Pydantic.
        # If so, we simulate mismatch by passing a summary where the
        # validator logic detects a discrepancy (e.g. rate vs n/events).
    )


@pytest.fixture
def continuous_summary_consistent() -> ABTestSummary:
    """
    A continuous outcome summary that is internally consistent:
    - Baseline: n=100, mean=10, std=2
    - Variant: n=100, mean=11, std=2.1
    - Reconstructed Welch t-test p-value ~ 0.003
    - Effect size (Cohen's d) ~ 0.49
    - Reported p-value: 0.003
    - Reported effect size: 0.49
    """
    return ABTestSummary(
        url="https://example.com/test6",
        test_type="continuous",
        baseline_n=100,
        baseline_mean=10.0,
        baseline_std=2.0,
        variant_n=100,
        variant_mean=11.0,
        variant_std=2.1,
        reported_p_value=0.003,
        reported_effect_size=0.49,
        reported_effect_size_type="cohens_d",
        baseline_rate=None,
        variant_rate=None,
    )


@pytest.fixture
def continuous_summary_p_mismatch() -> ABTestSummary:
    """
    Same as continuous_summary_consistent but with a reported p-value
    that differs significantly from the reconstructed one.
    """
    return ABTestSummary(
        url="https://example.com/test7",
        test_type="continuous",
        baseline_n=100,
        baseline_mean=10.0,
        baseline_std=2.0,
        variant_n=100,
        variant_mean=11.0,
        variant_std=2.1,
        reported_p_value=0.200,  # Large mismatch
        reported_effect_size=0.49,
        reported_effect_size_type="cohens_d",
        baseline_rate=None,
        variant_rate=None,
    )


# --------------------------------------------------------------------------
# Tests: p-value consistency
# --------------------------------------------------------------------------

def test_p_value_consistency_pass(logger_fixture):
    """
    When the absolute difference between reported and reconstructed p-value
    is <= 0.05, the check should pass (no flag).
    """
    summary = binary_summary_consistent()
    # Reconstructed p-value for this data is ~0.001 (z-test approx)
    # reported_p_value = 0.001
    # diff = 0
    result = check_p_value_consistency(summary, logger_fixture)
    assert result["flagged"] is False
    assert "p-value" not in result.get("reason", "")


def test_p_value_consistency_fail(logger_fixture):
    """
    When the absolute difference between reported and reconstructed p-value
    is > 0.05, the check should flag and include 'p-value' in the reason.
    """
    summary = binary_summary_p_mismatch()
    # Reconstructed ~0.001, reported 0.200 -> diff ~0.199 > 0.05
    result = check_p_value_consistency(summary, logger_fixture)
    assert result["flagged"] is True
    assert "p-value" in result.get("reason", "").lower()


# --------------------------------------------------------------------------
# Tests: effect-size consistency
# --------------------------------------------------------------------------

def test_effect_size_consistency_pass(logger_fixture):
    """
    When the relative difference between reported and reconstructed effect size
    is <= 5%, the check should pass.
    """
    summary = binary_summary_consistent()
    # Reconstructed effect size (absolute diff in rates) = 0.05
    # reported_effect_size = 0.05
    # relative diff = 0
    result = check_effect_size_consistency(summary, logger_fixture)
    assert result["flagged"] is False
    assert "effect size" not in result.get("reason", "")


def test_effect_size_consistency_fail(logger_fixture):
    """
    When the relative difference between reported and reconstructed effect size
    is > 5%, the check should flag and include 'effect size' in the reason.
    """
    summary = binary_summary_effect_size_mismatch()
    # Reconstructed = 0.05, reported = 0.08
    # relative diff = |0.08 - 0.05| / 0.05 = 0.6 = 60% > 5%
    result = check_effect_size_consistency(summary, logger_fixture)
    assert result["flagged"] is True
    assert "effect size" in result.get("reason", "").lower()


# --------------------------------------------------------------------------
# Tests: inequality p-value handling
# --------------------------------------------------------------------------

def test_inequality_p_value_handling_flagged(logger_fixture):
    """
    When the reported p-value is an inequality (e.g. 'p < 0.05'),
    the validator should flag it and include 'inequality' in the reason.
    """
    summary = binary_summary_inequality_p()
    result = handle_inequality_p_value(summary, logger_fixture)
    assert result["flagged"] is True
    assert "inequality" in result.get("reason", "").lower()


def test_inequality_p_value_handling_not_flagged(logger_fixture):
    """
    When the reported p-value is a numeric value, the check should not flag.
    """
    summary = binary_summary_consistent()
    result = handle_inequality_p_value(summary, logger_fixture)
    assert result["flagged"] is False


# --------------------------------------------------------------------------
# Tests: sample-size mismatch detection
# --------------------------------------------------------------------------

def test_sample_size_consistency_pass(logger_fixture):
    """
    When baseline_n, baseline_events, and baseline_rate are consistent
    (n * rate ≈ events), the check should pass.
    """
    summary = binary_summary_consistent()
    # 1000 * 0.10 = 100 events -> consistent
    result = check_sample_size_consistency(summary, logger_fixture)
    assert result["flagged"] is False
    assert "sample size" not in result.get("reason", "").lower()


def test_sample_size_consistency_fail(logger_fixture):
    """
    When baseline_n, baseline_events, and baseline_rate are inconsistent,
    the check should flag and include 'sample size' in the reason.
    """
    # Construct a summary with inconsistent data
    summary = ABTestSummary(
        url="https://example.com/test_inconsistent",
        test_type="binary",
        baseline_n=1000,
        baseline_events=100,
        variant_n=1000,
        variant_events=150,
        reported_p_value=0.001,
        reported_effect_size=0.05,
        reported_effect_size_type="absolute",
        baseline_rate=0.20,  # 1000 * 0.20 = 200, but events=100 -> inconsistent
        variant_rate=0.15,
    )
    result = check_sample_size_consistency(summary, logger_fixture)
    assert result["flagged"] is True
    assert "sample size" in result.get("reason", "").lower()


# --------------------------------------------------------------------------
# Tests: full record validation
# --------------------------------------------------------------------------

def test_validate_single_record_all_pass(logger_fixture):
    """
    A fully consistent record should produce an AuditRecord with no flags.
    """
    summary = binary_summary_consistent()
    audit_record = validate_single_record(summary, logger_fixture)
    assert isinstance(audit_record, AuditRecord)
    assert audit_record.url == summary.url
    assert audit_record.is_consistent is True
    assert audit_record.data_quality_warning is False
    assert audit_record.flags == []


def test_validate_single_record_p_value_flag(logger_fixture):
    """
    A record with p-value mismatch should be flagged and is_consistent=False.
    """
    summary = binary_summary_p_mismatch()
    audit_record = validate_single_record(summary, logger_fixture)
    assert audit_record.is_consistent is False
    assert "p-value" in str(audit_record.flags).lower()


def test_validate_single_record_effect_size_flag(logger_fixture):
    """
    A record with effect-size mismatch should be flagged and is_consistent=False.
    """
    summary = binary_summary_effect_size_mismatch()
    audit_record = validate_single_record(summary, logger_fixture)
    assert audit_record.is_consistent is False
    assert "effect size" in str(audit_record.flags).lower()


def test_validate_single_record_inequality_flag(logger_fixture):
    """
    A record with inequality p-value should be flagged.
    """
    summary = binary_summary_inequality_p()
    audit_record = validate_single_record(summary, logger_fixture)
    assert audit_record.is_consistent is False
    assert "inequality" in str(audit_record.flags).lower()


def test_validate_single_record_sample_size_warning(logger_fixture):
    """
    A record with sample-size inconsistency should have data_quality_warning=True.
    """
    summary = ABTestSummary(
        url="https://example.com/test_inconsistent",
        test_type="binary",
        baseline_n=1000,
        baseline_events=100,
        variant_n=1000,
        variant_events=150,
        reported_p_value=0.001,
        reported_effect_size=0.05,
        reported_effect_size_type="absolute",
        baseline_rate=0.20,  # inconsistent
        variant_rate=0.15,
    )
    audit_record = validate_single_record(summary, logger_fixture)
    assert audit_record.data_quality_warning is True
    assert "sample size" in str(audit_record.flags).lower()


# --------------------------------------------------------------------------
# Tests: run_validation (batch)
# --------------------------------------------------------------------------

def test_run_validation_batch(logger_fixture):
    """
    Run validation on a list of summaries and verify the output list
    contains the expected number of AuditRecord objects with correct flags.
    """
    summaries = [
        binary_summary_consistent(),
        binary_summary_p_mismatch(),
        binary_summary_effect_size_mismatch(),
        binary_summary_inequality_p(),
    ]
    audit_records = run_validation(summaries, logger_fixture)
    assert len(audit_records) == len(summaries)
    # Expected: 1 consistent, 3 inconsistent
    consistent_count = sum(1 for r in audit_records if r.is_consistent)
    assert consistent_count == 1


# --------------------------------------------------------------------------
# Tests: main (CLI entry point)
# --------------------------------------------------------------------------

def test_main_writes_output(tmp_path: Path, logger_fixture):
    """
    The main() entry point should read an input JSON of summaries,
    run validation, and write an audit_report.json to the specified output path.
    """
    # Prepare input data
    summaries = [
        binary_summary_consistent().model_dump(),
        binary_summary_p_mismatch().model_dump(),
    ]
    input_path = tmp_path / "input_summaries.json"
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f)

    output_path = tmp_path / "audit_report.json"

    # Run main
    sys.argv = [
        "test_main",
        "--input", str(input_path),
        "--output", str(output_path),
    ]
    main()

    # Verify output file exists and contains valid JSON
    assert output_path.exists()
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check structure
    assert isinstance(data, list)
    assert len(data) == 2
    # First record should be consistent, second inconsistent
    assert data[0]["is_consistent"] is True
    assert data[1]["is_consistent"] is False