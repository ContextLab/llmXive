import pytest
from pathlib import Path
import tempfile
import os

# Import the functions to test
from code.scr.update_spec_governance_fr009 import (
    remove_fr_009_from_spec,
    update_plan_md_for_fr009
)

def test_remove_fr_009_from_spec_removes_list_item():
    """Test that FR-009 is removed from a list item in spec.md."""
    spec_content = """
    ## Functional Requirements
    - [ ] FR-001: Requirement 1
    - [ ] FR-009: Low-level covariates exclusion
    - [ ] FR-010: Requirement 10
    """
    expected = """
    ## Functional Requirements
    - [ ] FR-001: Requirement 1

    - [ ] FR-010: Requirement 10
    """
    result = remove_fr_009_from_spec(spec_content)
    assert "FR-009" not in result
    assert "FR-001" in result
    assert "FR-010" in result

def test_remove_fr_009_from_spec_removes_header():
    """Test that FR-009 is removed if it appears as a header or definition line."""
    spec_content = """
    ## Functional Requirements
    FR-009: Compute low-level features like luminance and contrast.
    - [ ] FR-001: Requirement 1
    """
    result = remove_fr_009_from_spec(spec_content)
    assert "FR-009" not in result
    assert "FR-001" in result

def test_update_plan_md_adds_exclusion_note():
    """Test that plan.md gets updated with FR-009 exclusion note."""
    plan_content = """
    # Plan
    Some content.
    """
    result = update_plan_md_for_fr009(plan_content)
    assert "FR-009" in result
    assert "excluded" in result.lower()
    assert "SCR-002" in result

def test_update_plan_md_does_not_duplicate_note():
    """Test that the exclusion note is not added if it already exists."""
    existing_note = "- **Spec Contradiction**: Low-level covariates (FR-009) excluded..."
    plan_content = f"""
    # Plan
    Some content.
    {existing_note}
    """
    result = update_plan_md_for_fr009(plan_content)
    # Count occurrences of the key phrase to ensure no duplication
    count = result.count("FR-009")
    # Should appear only once in the existing note
    assert count == 1
    assert "excluded" in result.lower()
    assert "SCR-002" in result
