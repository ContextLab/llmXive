"""
Tests for documentation artifacts.
Ensures that required documentation files exist and contain expected content.
"""
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def test_readme_exists():
    """Test that README.md exists at the project root."""
    readme_path = PROJECT_ROOT / "README.md"
    assert readme_path.exists(), "README.md not found at project root"
    content = readme_path.read_text()
    assert "PROJ-540" in content, "README.md does not contain project ID"
    assert "doomscrolling" in content.lower(), "README.md missing topic keywords"

def test_docs_directory_exists():
    """Test that the docs directory exists."""
    docs_path = PROJECT_ROOT / "docs"
    assert docs_path.exists(), "docs/ directory not found"
    assert docs_path.is_dir(), "docs/ is not a directory"

def test_docs_readme_exists():
    """Test that docs/README.md exists."""
    docs_readme = PROJECT_ROOT / "docs" / "README.md"
    assert docs_readme.exists(), "docs/README.md not found"
    content = docs_readme.read_text()
    assert "Technical Specifications" in content, "docs/README.md missing technical specs"

def test_contributing_exists():
    """Test that docs/CONTRIBUTING.md exists."""
    contributing = PROJECT_ROOT / "docs" / "CONTRIBUTING.md"
    assert contributing.exists(), "docs/CONTRIBUTING.md not found"
    content = contributing.read_text()
    assert "Code Style" in content, "CONTRIBUTING.md missing style guide"

def test_architecture_exists():
    """Test that docs/ARCHITECTURE.md exists."""
    architecture = PROJECT_ROOT / "docs" / "ARCHITECTURE.md"
    assert architecture.exists(), "docs/ARCHITECTURE.md not found"
    content = architecture.read_text()
    assert "Pipeline Flow" in content, "ARCHITECTURE.md missing pipeline flow"

def test_results_exists():
    """Test that docs/RESULTS.md exists."""
    results = PROJECT_ROOT / "docs" / "RESULTS.md"
    assert results.exists(), "docs/RESULTS.md not found"
    content = results.read_text()
    assert "Key Findings" in content, "RESULTS.md missing key findings"

def test_faq_exists():
    """Test that docs/FAQ.md exists."""
    faq = PROJECT_ROOT / "docs" / "FAQ.md"
    assert faq.exists(), "docs/FAQ.md not found"
    content = faq.read_text()
    assert "Power limitation" in content, "FAQ.md missing power limitation question"