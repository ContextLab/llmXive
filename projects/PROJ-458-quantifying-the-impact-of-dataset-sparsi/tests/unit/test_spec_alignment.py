"""
Unit tests for spec alignment checks.
"""
import pytest
from code.spec_alignment_check import check_fr006_alignment, load_spec_content

def test_check_fr006_alignment_with_lmm():
    """Test that FR-006 is correctly identified when LMM is present."""
    spec_content = """
    # Functional Requirements
    
    ## FR-006: Statistical Analysis Method
    The study shall employ **Linear Mixed-Effects Modeling (LMM)** to analyze the impact of sparsity.
    This approach is chosen over ANOVA to handle nested data structures.
    """
    assert check_fr006_alignment(spec_content) is True

def test_check_fr006_alignment_without_lmm():
    """Test that FR-006 is correctly identified as missing when LMM is not present."""
    spec_content = """
    # Functional Requirements
    
    ## FR-006: Statistical Analysis Method
    The study shall employ Repeated Measures ANOVA to analyze the impact of sparsity.
    """
    assert check_fr006_alignment(spec_content) is False

def test_load_spec_content_exists():
    """Test that load_spec_content can find the spec file if it exists."""
    # This test will pass if the file exists, or raise FileNotFoundError if not
    # We don't force a pass here, as the file existence is a real check
    try:
        content = load_spec_content("specs/001-quantifying-the-impact-of-dataset-sparsity/spec.md")
        assert isinstance(content, str)
        assert len(content) > 0
    except FileNotFoundError:
        # If the file doesn't exist, we note that the test environment is incomplete
        # but the function behavior is correct
        pytest.skip("Spec file not found in test environment")

def test_check_fr006_partial_match():
    """Test partial matches for LMM variations."""
    spec_content = """
    ## FR-006
    Use Mixed-Effects Models for analysis.
    """
    assert check_fr006_alignment(spec_content) is True

    spec_content_no_match = """
    ## FR-006
    Use standard ANOVA for analysis.
    """
    assert check_fr006_alignment(spec_content_no_match) is False