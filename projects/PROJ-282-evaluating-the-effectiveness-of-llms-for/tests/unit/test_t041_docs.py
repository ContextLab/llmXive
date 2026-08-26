"""
Unit tests for T041: Documentation Updates.
Verifies that all required documentation files exist and contain expected content.
"""
import os
import pytest
from pathlib import Path

# Define expected documentation files
EXPECTED_DOCS = [
    "README.md",
    "docs/PIPELINE_GUIDE.md",
    "docs/REPRODUCIBILITY.md",
    "docs/ARCHITECTURE.md",
    "docs/CONTRIBUTING.md",
    "docs/USAGE_EXAMPLES.md"
]

# Define expected key phrases in each file
EXPECTED_CONTENT = {
    "README.md": ["llmXive", "VulDeePecker", "JSVulnDB", "NIST Juliet", "CPU-Optimized"],
    "docs/PIPELINE_GUIDE.md": ["DAG", "Data Ingestion", "Feature Extraction", "Statistical Methods"],
    "docs/REPRODUCIBILITY.md": ["Determinism", "Seeds", "Artifact Integrity", "Data Provenance"],
    "docs/ARCHITECTURE.md": ["Data Layer", "Model Layer", "Analysis Layer", "Data Flow"],
    "docs/CONTRIBUTING.md": ["Development Setup", "Adding a New Dataset", "Code Style", "Testing"],
    "docs/USAGE_EXAMPLES.md": ["Running the Full Pipeline", "Custom Configuration", "Inspecting Results"]
}

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def test_documentation_files_exist():
    """Verify all required documentation files exist."""
    project_root = get_project_root()
    missing_files = []

    for doc_file in EXPECTED_DOCS:
        full_path = project_root / doc_file
        if not full_path.exists():
            missing_files.append(doc_file)

    assert not missing_files, f"Missing documentation files: {missing_files}"

def test_readme_content():
    """Verify README.md contains key project information."""
    project_root = get_project_root()
    readme_path = project_root / "README.md"

    assert readme_path.exists(), "README.md not found"

    content = readme_path.read_text()
    assert "llmXive" in content, "README.md missing project name"
    assert "VulDeePecker" in content, "README.md missing VulDeePecker reference"
    assert "JSVulnDB" in content, "README.md missing JSVulnDB reference"
    assert "NIST Juliet" in content, "README.md missing NIST Juliet reference"
    assert "CPU-Optimized" in content, "README.md missing CPU optimization note"

def test_pipeline_guide_content():
    """Verify PIPELINE_GUIDE.md contains architecture details."""
    project_root = get_project_root()
    guide_path = project_root / "docs/PIPELINE_GUIDE.md"

    assert guide_path.exists(), "PIPELINE_GUIDE.md not found"

    content = guide_path.read_text()
    assert "DAG" in content, "PIPELINE_GUIDE.md missing DAG reference"
    assert "Data Ingestion" in content, "PIPELINE_GUIDE.md missing data ingestion section"
    assert "Feature Extraction" in content, "PIPELINE_GUIDE.md missing feature extraction section"

def test_reproducibility_content():
    """Verify REPRODUCIBILITY.md contains reproducibility protocols."""
    project_root = get_project_root()
    repro_path = project_root / "docs/REPRODUCIBILITY.md"

    assert repro_path.exists(), "REPRODUCIBILITY.md not found"

    content = repro_path.read_text()
    assert "Determinism" in content, "REPRODUCIBILITY.md missing determinism section"
    assert "Artifact Integrity" in content, "REPRODUCIBILITY.md missing artifact integrity section"
    assert "Data Provenance" in content, "REPRODUCIBILITY.md missing data provenance section"

def test_requirements_txt_exists():
    """Verify requirements.txt exists and contains expected dependencies."""
    project_root = get_project_root()
    req_path = project_root / "requirements.txt"

    assert req_path.exists(), "requirements.txt not found"

    content = req_path.read_text()
    assert "transformers" in content, "requirements.txt missing transformers"
    assert "torch" in content, "requirements.txt missing torch"
    assert "pandas" in content, "requirements.txt missing pandas"
    assert "statsmodels" in content, "requirements.txt missing statsmodels"
    assert "tree-sitter" in content, "requirements.txt missing tree-sitter"
    assert "radon" in content, "requirements.txt missing radon"

def test_all_expected_content_present():
    """Verify all expected content phrases are present in their respective files."""
    project_root = get_project_root()

    for doc_file, phrases in EXPECTED_CONTENT.items():
        full_path = project_root / doc_file
        if full_path.exists():
            content = full_path.read_text()
            for phrase in phrases:
                assert phrase in content, f"Missing '{phrase}' in {doc_file}"
        else:
            pytest.fail(f"File {doc_file} not found for content check")