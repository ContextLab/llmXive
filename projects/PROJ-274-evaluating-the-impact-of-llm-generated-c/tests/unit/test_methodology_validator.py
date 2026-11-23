"""
Unit tests for the Methodology Validator (T070c).
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from code.validation.methodology_validator import validate_research_content

def test_validate_forbidden_decision_tree():
    """Test that a document containing a 'decision tree' is flagged as invalid."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
        # Research Methodology
        
        We will use a decision tree to select the appropriate statistical test.
        If normality is met, we use t-test. Otherwise, we use Mann-Whitney.
        """)
        temp_path = Path(f.name)

    try:
        result = validate_research_content(temp_path)
        assert result["status"] == "invalid"
        assert "decision tree" in result["forbidden_patterns_found"]
    finally:
        os.unlink(temp_path)

def test_validate_pre_specified_welch():
    """Test that a document with pre-specified Welch's ANOVA is valid."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
        # Research Methodology
        
        1. Pre-specified Analysis Approach: Welch's ANOVA is the ONLY primary test.
        2. Diagnostics: Levene's and Shapiro-Wilk tests are for POST-HOC reporting ONLY.
        3. Power Analysis: Variance estimation focus.
        
        The decision tree for test selection is REMOVED.
        """)
        temp_path = Path(f.name)

    try:
        result = validate_research_content(temp_path)
        assert result["status"] == "valid"
        assert "decision tree" not in result["forbidden_patterns_found"]
        assert "welch's anova" in result["required_patterns_found"]
        assert "pre-specified" in result["required_patterns_found"]
    finally:
        os.unlink(temp_path)

def test_validate_missing_file():
    """Test that a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        validate_research_content(Path("/nonexistent/file.md"))