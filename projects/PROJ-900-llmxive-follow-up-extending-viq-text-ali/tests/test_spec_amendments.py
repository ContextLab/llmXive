"""
Tests for T036c: Spec Amendments Update.
Verifies that the update script correctly injects Decision Record 002 references.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from update_spec_amendments import update_spec_content

def test_fr003_exclusion_added():
    """Test that FR-003 exclusion text is added if missing."""
    content = """
    # Specification
    ## FR-003: Data Exclusion
    The study excludes datasets with incompatible modalities.
    """
    result = update_spec_content(content)
    assert "ChestX-ray14" in result
    assert "Decision Record 001" in result
    assert "excluded" in result.lower()

def test_fr004_ground_truth_added():
    """Test that FR-004 native ground truth text is added if missing."""
    content = """
    ## FR-004: Ground Truth
    The study uses upsampled ground truth for baseline.
    """
    result = update_spec_content(content)
    assert "Native 1024x1024 ground truth used per Decision Record 002" in result

def test_sc004_paired_test_added():
    """Test that SC-004 paired test text is added if missing."""
    content = """
    ## SC-004: Statistical Test
    A one-sample t-test is used for evaluation.
    """
    result = update_spec_content(content)
    assert "Paired t-test or Wilcoxon signed-rank test used per Decision Record 002" in result

def test_no_duplicate_amendments():
    """Test that the script does not add duplicates if text already exists."""
    content = """
    ## FR-004: Ground Truth
    Native 1024x1024 ground truth used per Decision Record 002.
    """
    result = update_spec_content(content)
    # Count occurrences of the specific string
    count = result.count("Native 1024x1024 ground truth used per Decision Record 002")
    assert count == 1, f"Expected 1 occurrence, found {count}"

def test_full_spec_update():
    """Test update on a more realistic spec structure."""
    content = """
    # ViQ Resolution Invariance Study
    
    ## Functional Requirements
    FR-001: Resolution Invariance
    FR-003: Exclude ChestX-ray14
    FR-004: Use upsampled baseline
    
    ## Statistical Constraints
    SC-001: Normality check
    SC-004: One-sample t-test
    """
    result = update_spec_content(content)
    
    # Verify all three amendments are present
    assert "ChestX-ray14" in result and "Decision Record 001" in result
    assert "Native 1024x1024 ground truth used per Decision Record 002" in result
    assert "Paired t-test or Wilcoxon signed-rank test used per Decision Record 002" in result