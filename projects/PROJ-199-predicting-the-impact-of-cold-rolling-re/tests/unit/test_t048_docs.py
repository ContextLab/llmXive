"""
Unit tests for T048: Documentation Updates.

These tests verify that the required documentation artifacts exist
and contain the mandatory content regarding model limitations,
associational framing, and sensitivity analysis methodology.
"""
import os
import re
from pathlib import Path

# Base path for docs
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"

def test_readme_exists():
    """Verify README.md exists."""
    readme = DOCS_DIR / "README.md"
    assert readme.exists(), "docs/README.md does not exist"

def test_readme_contains_associational_framing():
    """Verify README.md discusses associational nature of models."""
    readme = DOCS_DIR / "README.md"
    content = readme.read_text()
    
    # Check for key phrases
    assert "associational" in content.lower(), "README must mention 'associational' relationships"
    assert "caus" not in content.lower() or "causal" in content.lower(), "README should clarify causal vs associational"
    assert "disclaimer" in content.lower() or "limitation" in content.lower(), "README should include limitations section"

def test_readme_contains_sensitivity_methodology():
    """Verify README.md documents sensitivity analysis methodology."""
    readme = DOCS_DIR / "README.md"
    content = readme.read_text()
    
    assert "sensitivity" in content.lower(), "README must mention sensitivity analysis"
    assert "tolerance" in content.lower(), "README must mention tolerance sweep"
    assert "0.02" in content, "README must mention the 0.02 R² variation threshold"

def test_model_limitations_exists():
    """Verify MODEL_LIMITATIONS.md exists."""
    limits = DOCS_DIR / "MODEL_LIMITATIONS.md"
    assert limits.exists(), "docs/MODEL_LIMITATIONS.md does not exist"

def test_model_limitations_content():
    """Verify MODEL_LIMITATIONS.md contains required sections."""
    limits = DOCS_DIR / "MODEL_LIMITATIONS.md"
    content = limits.read_text()
    
    # Check for specific limitations
    assert "associational" in content.lower(), "Must discuss associational framing"
    assert "extrapolation" in content.lower(), "Must discuss extrapolation risks"
    assert "missing" in content.lower() and "variable" in content.lower(), "Must discuss missing microstructural variables"
    assert "symmetry" in content.lower(), "Must discuss symmetry constraints"
    assert "confidence" in content.lower(), "Must discuss confidence penalties"

def test_sensitivity_analysis_method_exists():
    """Verify SENSITIVITY_ANALYSIS_METHOD.md exists."""
    method = DOCS_DIR / "SENSITIVITY_ANALYSIS_METHOD.md"
    assert method.exists(), "docs/SENSITIVITY_ANALYSIS_METHOD.md does not exist"

def test_sensitivity_analysis_method_content():
    """Verify SENSITIVITY_ANALYSIS_METHOD.md details the methodology."""
    method = DOCS_DIR / "SENSITIVITY_ANALYSIS_METHOD.md"
    content = method.read_text()
    
    # Check for methodology details
    assert "tolerance" in content.lower(), "Must describe tolerance sweep"
    assert "0.01" in content or "0.05" in content or "0.1" in content, "Must list tolerance values"
    assert "r2" in content.lower(), "Must mention R² metric"
    assert "0.02" in content, "Must mention the 0.02 threshold"
    assert "robust" in content.lower(), "Must define robustness criteria"
    assert "sensitivity_analysis.csv" in content, "Must reference the output file"

def test_no_placeholder_text():
    """Verify documentation does not contain placeholder text."""
    for doc_file in ["README.md", "MODEL_LIMITATIONS.md", "SENSITIVITY_ANALYSIS_METHOD.md"]:
        file_path = DOCS_DIR / doc_file
        if file_path.exists():
            content = file_path.read_text()
            assert "[Insert" not in content, f"{doc_file} contains placeholder text '[Insert...'"
            assert "TODO" not in content, f"{doc_file} contains 'TODO'"
            assert "placeholder" not in content.lower(), f"{doc_file} contains 'placeholder'"