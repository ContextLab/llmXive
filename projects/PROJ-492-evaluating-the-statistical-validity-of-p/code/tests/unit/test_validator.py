import pytest
from pathlib import Path
import json
import sys
from datetime import datetime

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.models.data_models import ABTestSummary
from code.src.audit.validator import (
    validate_summary,
    validate_all_summaries,
    filter_for_prevalence,
    write_audit_report,
    detect_sample_size_mismatch,
    check_p_value_consistency,
    check_effect_size_consistency,
    ABSOLUTE_P_DIFFERENCE_THRESHOLD,
    RELATIVE_EFFECT_SIZE_THRESHOLD
)

def test_p_value_consistency_within_threshold():
    """Test that p-values within threshold are marked consistent."""
    summary = ABTestSummary(
        url="http://example.com/test1",
        domain="example.com",
        p_value_reported=0.04,
        p_value_reconstructed=0.042,
        effect_size_reported=0.10,
        effect_size_reconstructed=0.102,
        sample_size_control=100,
        sample_size_treatment=100
    )
    record = validate_summary(summary)
    assert record.is_consistent is True
    assert "p_value_inconsistent" not in record.flags

def test_p_value_consistency_outside_threshold():
    """Test that p-values outside threshold are marked inconsistent."""
    summary = ABTestSummary(
        url="http://example.com/test2",
        domain="example.com",
        p_value_reported=0.04,
        p_value_reconstructed=0.10, # Diff = 0.06 > 0.05
        effect_size_reported=0.10,
        effect_size_reconstructed=0.102,
        sample_size_control=100,
        sample_size_treatment=100
    )
    record = validate_summary(summary)
    assert record.is_consistent is False
    assert "p_value_inconsistent" in record.flags

def test_effect_size_consistency_within_threshold():
    """Test that effect sizes within 5% relative diff are consistent."""
    summary = ABTestSummary(
        url="http://example.com/test3",
        domain="example.com",
        p_value_reported=0.04,
        p_value_reconstructed=0.041,
        effect_size_reported=0.10,
        effect_size_reconstructed=0.104, # 4% diff
        sample_size_control=100,
        sample_size_treatment=100
    )
    record = validate_summary(summary)
    assert record.is_consistent is True
    assert "effect_size_inconsistent" not in record.flags

def test_effect_size_consistency_outside_threshold():
    """Test that effect sizes outside 5% relative diff are inconsistent."""
    summary = ABTestSummary(
        url="http://example.com/test4",
        domain="example.com",
        p_value_reported=0.04,
        p_value_reconstructed=0.041,
        effect_size_reported=0.10,
        effect_size_reconstructed=0.16, # 60% diff
        sample_size_control=100,
        sample_size_treatment=100
    )
    record = validate_summary(summary)
    assert record.is_consistent is False
    assert "effect_size_inconsistent" in record.flags

def test_sample_size_mismatch_detection():
    """Test detection of sample size mismatch."""
    # Missing total
    summary1 = ABTestSummary(
        url="http://example.com/test5",
        domain="example.com",
        p_value_reported=0.04,
        p_value_reconstructed=0.041,
        effect_size_reported=0.10,
        effect_size_reconstructed=0.101,
        sample_size_control=100,
        sample_size_treatment=100,
        sample_size_total=None
    )
    # Total doesn't match sum
    summary2 = ABTestSummary(
        url="http://example.com/test6",
        domain="example.com",
        p_value_reported=0.04,
        p_value_reconstructed=0.041,
        effect_size_reported=0.10,
        effect_size_reconstructed=0.101,
        sample_size_control=100,
        sample_size_treatment=100,
        sample_size_total=250 # Expected 200
    )
    # Missing control size
    summary3 = ABTestSummary(
        url="http://example.com/test7",
        domain="example.com",
        p_value_reported=0.04,
        p_value_reconstructed=0.041,
        effect_size_reported=0.10,
        effect_size_reconstructed=0.101,
        sample_size_control=None,
        sample_size_treatment=100
    )

    assert detect_sample_size_mismatch(summary1) is True
    assert detect_sample_size_mismatch(summary2) is True
    assert detect_sample_size_mismatch(summary3) is True

def test_sample_size_mismatch_flagging_and_exclusion():
    """Test that sample size mismatches are flagged and excluded from prevalence."""
    summary_match = ABTestSummary(
        url="http://example.com/match",
        domain="example.com",
        p_value_reported=0.04,
        p_value_reconstructed=0.041,
        effect_size_reported=0.10,
        effect_size_reconstructed=0.101,
        sample_size_control=100,
        sample_size_treatment=100,
        sample_size_total=200
    )
    summary_mismatch = ABTestSummary(
        url="http://example.com/mismatch",
        domain="example.com",
        p_value_reported=0.04,
        p_value_reconstructed=0.041,
        effect_size_reported=0.10,
        effect_size_reconstructed=0.101,
        sample_size_control=100,
        sample_size_treatment=100,
        sample_size_total=300
    )

    records = validate_all_summaries([summary_match, summary_mismatch])
    
    match_record = next(r for r in records if "match" in r.url)
    mismatch_record = next(r for r in records if "mismatch" in r.url)

    assert match_record.is_consistent is True
    assert "sample_size_mismatch" not in match_record.flags

    assert mismatch_record.is_consistent is False # Inconsistent due to mismatch flag
    assert "sample_size_mismatch" in mismatch_record.flags
    assert any("data_quality_warning" in w for w in mismatch_record.warnings)

    # Filter for prevalence
    prevalence_records = filter_for_prevalence(records)
    assert len(prevalence_records) == 1
    assert prevalence_records[0].url == "http://example.com/match"

def test_write_audit_report(tmp_path):
    """Test writing audit report to JSON."""
    summaries = [
        ABTestSummary(
            url="http://example.com/test1",
            domain="example.com",
            p_value_reported=0.04,
            p_value_reconstructed=0.041,
            effect_size_reported=0.10,
            effect_size_reconstructed=0.101,
            sample_size_control=100,
            sample_size_treatment=100
        )
    ]
    records = validate_all_summaries(summaries)
    output_file = tmp_path / "audit_report.json"
    
    write_audit_report(records, output_file)
    
    assert output_file.exists()
    with open(output_file) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["url"] == "http://example.com/test1"
    assert data[0]["is_consistent"] is True
