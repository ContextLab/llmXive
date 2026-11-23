"""
Contract test for report content validation (US3).

This test ensures the generated final report adheres to the associational framing
requirement (FR-004) and explicitly avoids causal language.
"""
import re
from pathlib import Path

import pytest

# Path to the expected report artifact relative to project root
REPORT_PATH = Path("artifacts/reports/final_report.md")

# Forbidden causal phrases (case-insensitive)
FORBIDDEN_CAUSAL_PHRASES = [
    r"\bcasue\b",
    r"\bcauses\b",
    r"\bcausal\b",
    r"\bdetermine\b",
    r"\bdetermines\b",
    r"\bdetermined\b",
    r"\bprove\b",
    r"\bproves\b",
    r"\bproven\b",
    r"\bconfirm\b",
    r"\bconfirms\b",
    r"\bconfirmed\b",
    r"\bimpact\b", # Often used causally, though context matters; strict contract
    r"\binfluence\b", # Same as impact
    r"\beffect\b", # Same as impact
]

# Required disclaimer phrase
REQUIRED_DISCLAIMER = "These findings are associational only"


def _load_report_content() -> str:
    """Load the content of the final report."""
    if not REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Report artifact not found at {REPORT_PATH}. "
            "Ensure T041 (Generate final report) has been executed successfully."
        )
    return REPORT_PATH.read_text(encoding="utf-8")


def test_report_contains_associational_disclaimer():
    """
    Contract Test: Verify the report contains the mandatory disclaimer.
    
    Requirement: FR-004 (Associational Framing)
    """
    content = _load_report_content()
    assert REQUIRED_DISCLAIMER in content, (
        f"Report is missing the mandatory disclaimer: '{REQUIRED_DISCLAIMER}'. "
        "Add this exact phrase to the report generation logic in code/report.py."
    )


def test_report_avoids_causal_language():
    """
    Contract Test: Verify the report does not contain forbidden causal language.
    
    Requirement: FR-004 (Associational Framing)
    """
    content = _load_report_content()
    content_lower = content.lower()
    
    violations = []
    for pattern in FORBIDDEN_CAUSAL_PHRASES:
        # Use re.search to find the pattern anywhere in the text
        if re.search(pattern, content_lower):
            violations.append(pattern)
    
    assert not violations, (
        f"Report contains forbidden causal language matching patterns: {violations}. "
        "Review code/report.py to ensure findings are described as associations, "
        "correlations, or predictive relationships, not causal effects."
    )


def test_report_structure_valid():
    """
    Basic contract test to ensure the report is not empty and has markdown structure.
    """
    content = _load_report_content()
    assert len(content.strip()) > 0, "Report file is empty."
    # Check for at least one header to ensure it's a markdown document
    assert re.search(r"^#{1,6}\s+", content, re.MULTILINE), (
        "Report does not appear to be a valid Markdown document (no headers found)."
    )