"""
Tests to verify the existence and basic validity of documentation artifacts.
"""
import os
import pytest
from pathlib import Path

DOCS_ROOT = Path(__file__).parent.parent / "docs"

REQUIRED_DOCS = [
    "README.md",
    "DATA_MODEL.md",
    "API_USAGE.md",
    "QUICKSTART.md",
    "ARCHITECTURE.md"
]

@pytest.mark.parametrize("doc", REQUIRED_DOCS)
def test_documentation_file_exists(doc):
    """Ensure all required documentation files exist."""
    doc_path = DOCS_ROOT / doc
    assert doc_path.exists(), f"Documentation file missing: {doc_path}"
    assert doc_path.stat().st_size > 0, f"Documentation file is empty: {doc_path}"

def test_readme_contains_project_title():
    """Ensure README contains the project title."""
    readme_path = DOCS_ROOT / "README.md"
    content = readme_path.read_text()
    assert "llmXive" in content, "README.md must mention 'llmXive'."
    assert "Network Structure" in content, "README.md must mention the project topic."

def test_data_model_documentation_structure():
    """Ensure DATA_MODEL.md contains key entity definitions."""
    data_model_path = DOCS_ROOT / "DATA_MODEL.md"
    content = data_model_path.read_text()
    required_entities = ["Participant", "StructuralConnectome", "AvalancheRecord"]
    for entity in required_entities:
        assert entity in content, f"DATA_MODEL.md must define the {entity} entity."

def test_api_usage_documentation_examples():
    """Ensure API_USAGE.md contains code examples."""
    api_usage_path = DOCS_ROOT / "API_USAGE.md"
    content = api_usage_path.read_text()
    assert "from" in content and "import" in content, "API_USAGE.md must contain import statements."
    assert "def" in content or "simulate_eeg" in content or "run_metrics" in content, \
        "API_USAGE.md must contain function usage examples."
