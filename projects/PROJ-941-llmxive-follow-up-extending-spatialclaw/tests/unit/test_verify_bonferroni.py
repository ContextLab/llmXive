"""
Unit tests for verify_bonferroni.py
"""
import pytest
import os
import tempfile
from pathlib import Path
from code.stats.verify_bonferroni import (
    apply_bonferroni_correction,
    verify_bonferroni_correction,
    parse_markdown_report
)

def test_apply_bonferroni_correction():
    # n_tests = 3
    assert apply_bonferroni_correction(0.01, 3) == 0.03
    assert apply_bonferroni_correction(0.05, 3) == 0.15
    assert apply_bonferroni_correction(0.5, 3) == 1.0  # Capped at 1.0
    assert apply_bonferroni_correction(0.34, 3) == 1.0  # 1.02 capped

def test_verify_bonferroni_logic():
    # Mock data simulating a correct report
    mock_results = {
        "occlusion": {"raw_p": 0.02, "reported_corrected_p": 0.06},
        "depth": {"raw_p": 0.03, "reported_corrected_p": 0.09},
        "relative": {"raw_p": 0.01, "reported_corrected_p": 0.03}
    }
    
    is_valid, messages = verify_bonferroni_correction(mock_results)
    assert is_valid is True
    assert len(messages) == 3

def test_verify_bonferroni_failure():
    # Mock data with a mismatch
    mock_results = {
        "occlusion": {"raw_p": 0.02, "reported_corrected_p": 0.05}, # Should be 0.06
        "depth": {"raw_p": 0.03, "reported_corrected_p": 0.09},
        "relative": {"raw_p": 0.01, "reported_corrected_p": 0.03}
    }
    
    is_valid, messages = verify_bonferroni_correction(mock_results)
    assert is_valid is False
    assert any("MISMATCH" in msg for msg in messages)

def test_parse_markdown_report():
    # Simulate a valid table row from the report
    mock_md = """
    # Statistical Report
    | Task Type | Test | Statistic | Raw P-value | Bonferroni Corrected P-value |
    | occlusion | Wilcoxon | 12.5 | 0.03 | 0.09 |
    | depth | t-test | 2.1 | 0.04 | 0.12 |
    """
    
    results = parse_markdown_report(mock_md)
    assert "occlusion" in results
    assert results["occlusion"]["raw_p"] == 0.03
    assert results["occlusion"]["reported_corrected_p"] == 0.09
    assert "depth" in results
    assert results["depth"]["raw_p"] == 0.04
    assert results["depth"]["reported_corrected_p"] == 0.12

def test_parse_markdown_report_no_data():
    mock_md = """
    # Statistical Report
    No tables here.
    """
    results = parse_markdown_report(mock_md)
    assert len(results) == 0