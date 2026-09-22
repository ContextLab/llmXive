"""
Unit tests for the Spec Amender (T001).
These tests verify that the spec_amender.py correctly applies the required patches.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from spec_amender import apply_patch, verify_amendments, main

def create_mock_spec_content():
    """Returns a mock spec.md content with the known broken text."""
    return """
# Specification: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

## 2. Functional Requirements

### FR-001: Prompt Generation and Complexity Levels
System MUST generate multiple prompt variants per HumanEval problem. The research question is: How does the framing of microtasks... (garbage text here).

### FR-005: Statistical Analysis
System MUST perform statistical analysis using ANOVA or Kruskal-Wallis to handle nested data structures.

### FR-012: Covariate Adjustment
System MUST control for code length (lines of code) when evaluating readability metrics.

## 3. User Stories

### US-1: Generate and Evaluate Code from Multiple Prompt Complexity Levels
...
"""

def test_apply_patch_fr005():
    """Test that FR-005 is updated to LMM."""
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "spec.md"
        spec_path.write_text(create_mock_spec_content())
        
        # Apply the specific correction for FR-005
        corrections = [
            ("FR-005", "ANOVA or Kruskal-Wallis", "Linear Mixed Models (LMM)")
        ]
        
        result = apply_patch(spec_path, corrections)
        assert result is True
        
        content = spec_path.read_text()
        assert "Linear Mixed Models (LMM)" in content
        assert "ANOVA or Kruskal-Wallis" not in content

def test_apply_patch_fr012():
    """Test that FR-012 is updated to prompt token count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "spec.md"
        spec_path.write_text(create_mock_spec_content())
        
        corrections = [
            ("FR-012", "code length (lines of code)", "prompt token count")
        ]
        
        result = apply_patch(spec_path, corrections)
        assert result is True
        
        content = spec_path.read_text()
        assert "prompt token count" in content
        assert "code length (lines of code)" not in content

def test_verify_amendments():
    """Test the verification function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "spec.md"
        # Write a correct spec
        correct_spec = """
# Specification
## FR-001
simple ≤ 50 tokens, degenerate > 500 tokens.
## FR-005
Linear Mixed Models (LMM)
## FR-012
prompt token count
## Assumptions
HumanEval availability
"""
        spec_path.write_text(correct_spec)
        
        success, missing = verify_amendments(spec_path)
        assert success is True
        assert len(missing) == 0

def test_verify_amendments_missing():
    """Test verification when items are missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        spec_path = Path(tmpdir) / "spec.md"
        incomplete_spec = """
# Specification
## FR-001
simple ≤ 50 tokens.
"""
        spec_path.write_text(incomplete_spec)
        
        success, missing = verify_amendments(spec_path)
        assert success is False
        assert "FR-005 LMM" in missing
        assert "FR-012 Token Covariate" in missing