"""
Unit tests for verify_associational_framing.py
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from verify_associational_framing import (
    check_framing_in_text,
    verify_final_report,
    CAUSAL_KEYWORDS,
    ASSOCIATIONAL_KEYWORDS
)

def test_causal_keyword_detection():
    """Test that causal keywords are detected."""
    text = "This study proves that code ownership causes bugs."
    violations = check_framing_in_text(text, context="Test")
    
    assert len(violations) > 0
    assert any(v["type"] == "causal_language" for v in violations)
    assert any("prove" in v.get("match", "").lower() or "cause" in v.get("match", "").lower() for v in violations)

def test_associational_keyword_acceptance():
    """Test that associational keywords do not trigger violations."""
    text = "This study shows an association between code ownership and bug density."
    violations = check_framing_in_text(text, context="Test")
    
    # Should not have causal violations
    causal_violations = [v for v in violations if v["type"] == "causal_language"]
    assert len(causal_violations) == 0

def test_missing_associational_framing_in_conclusion():
    """Test that conclusions without associational language are flagged."""
    text = "We found a link. It is strong."
    violations = check_framing_in_text(text, context="Section: Conclusions")
    
    # Should flag missing associational framing
    assert any(v["type"] == "missing_associational_framing" for v in violations)

def test_verify_final_report_missing_file():
    """Test verification with a non-existent file."""
    success, violations = verify_final_report(Path("/nonexistent/path.json"))
    
    assert success is False
    assert any(v["type"] == "file_not_found" for v in violations)

def test_verify_final_report_valid_framing():
    """Test verification with a correctly framed report."""
    report_data = {
        "metadata": {
            "framing": "associational rather than causal"
        },
        "findings": "We observed a correlation between ownership and quality.",
        "conclusions": "The results suggest an associational relationship."
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(report_data, f)
        temp_path = Path(f.name)
    
    try:
        success, violations = verify_final_report(temp_path)
        # Should pass (no violations)
        assert success is True
        assert len(violations) == 0
    finally:
        temp_path.unlink()

def test_verify_final_report_invalid_framing():
    """Test verification with a causally framed report."""
    report_data = {
        "metadata": {
            "framing": "causal impact analysis"
        },
        "findings": "Ownership causes bugs.",
        "conclusions": "We proved that ownership drives quality."
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(report_data, f)
        temp_path = Path(f.name)
    
    try:
        success, violations = verify_final_report(temp_path)
        # Should fail
        assert success is False
        assert len(violations) > 0
    finally:
        temp_path.unlink()