import pytest
import logging
import sys
from pathlib import Path
import tempfile
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.verify_methodology import find_section_5, verify_alignment

@pytest.fixture
def temp_spec_file():
    """Create a temporary spec.md file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
# Spec Document

## Section 1: Introduction
Some intro text.

## Section 5: Methodological Notes

This section describes the Revised Approach for the analysis.
The Synthetic Cohort approach was rejected as methodologically invalid.
We do not use Synthetic Cohort because it introduces confounding.

## Section 6: Conclusion
Final thoughts.
""")
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def temp_spec_missing_section():
    """Create a temp spec without Section 5."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
# Spec Document

## Section 1: Introduction
Some intro text.

## Section 6: Conclusion
Final thoughts.
""")
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def temp_spec_bad_synthetic():
    """Create a temp spec where Synthetic Cohort is proposed, not rejected."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""
# Spec Document

## Section 5: Methodological Notes

We will use the Revised Approach.
We will also implement the Synthetic Cohort to match datasets.

## Section 6: Conclusion
""")
        yield Path(f.name)
    os.unlink(f.name)

def test_find_section_5_exists(temp_spec_file):
    content = find_section_5(temp_spec_file)
    assert content != ""
    assert "Revised Approach" in content
    assert "Synthetic Cohort" in content

def test_find_section_5_missing(temp_spec_missing_section):
    content = find_section_5(temp_spec_missing_section)
    assert content == ""

def test_verify_alignment_good(temp_spec_file):
    content = find_section_5(temp_spec_file)
    result = verify_alignment(content)
    
    assert result["has_revised_approach"] is True
    assert result["synthetic_cohort_context_correct"] is True
    assert len(result["errors"]) == 0

def test_verify_alignment_bad_synthetic(temp_spec_bad_synthetic):
    content = find_section_5(temp_spec_bad_synthetic)
    result = verify_alignment(content)
    
    assert result["has_revised_approach"] is True
    assert result["synthetic_cohort_context_correct"] is False
    assert len(result["errors"]) > 0
    assert any("Synthetic Cohort" in err and "rejection" in err for err in result["errors"])

def test_verify_alignment_empty_content():
    result = verify_alignment("")
    assert len(result["errors"]) > 0
    assert "empty" in result["errors"][0].lower()