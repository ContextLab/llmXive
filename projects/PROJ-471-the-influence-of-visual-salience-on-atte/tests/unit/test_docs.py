"""
Unit tests for documentation completeness.
Verifies that required documentation files exist and contain expected content.
"""
import os
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"

REQUIRED_DOCS = [
    "scr_001_weapons_exclusion.md",
    "scr_002_lowlevel_covariates_exclusion.md",
    "scr_003_deepgaze_fallback.md",
    "implementation_notes.md",
    "pipeline_overview.md",
    "api_reference.md",
    "contributing.md",
]

def test_readme_exists():
    """Test that README.md exists in the project root."""
    readme = PROJECT_ROOT / "README.md"
    assert readme.exists(), "README.md must exist in the project root."
    content = readme.read_text()
    assert "PROJ-471" in content, "README.md must contain project ID."
    assert "SCR-001" in content, "README.md must reference governance SCRs."

@pytest.mark.parametrize("doc_file", REQUIRED_DOCS)
def test_required_docs_exist(doc_file):
    """Test that all required documentation files exist."""
    doc_path = DOCS_DIR / doc_file
    assert doc_path.exists(), f"Required documentation file {doc_file} is missing."
    assert doc_path.stat().st_size > 0, f"Documentation file {doc_file} is empty."

def test_scr_content_validity():
    """Test that SCR documents contain required fields."""
    scr_files = [
        ("scr_001_weapons_exclusion.md", ["Reason", "Impact", "Action"]),
        ("scr_002_lowlevel_covariates_exclusion.md", ["Reason", "Impact", "Action"]),
        ("scr_003_deepgaze_fallback.md", ["Reason", "Impact", "Action"]),
    ]

    for filename, required_fields in scr_files:
        doc_path = DOCS_DIR / filename
        content = doc_path.read_text()
        for field in required_fields:
            assert field in content, f"SCR {filename} must contain '{field}' section."

def test_api_reference_lists_modules():
    """Test that API reference lists key modules."""
    api_doc = DOCS_DIR / "api_reference.md"
    content = api_doc.read_text()
    assert "code/config.py" in content, "API reference must list config.py."
    assert "code/ingestion/salience_gen.py" in content, "API reference must list salience_gen.py."
    assert "code/analysis/lmm_fit.py" in content, "API reference must list lmm_fit.py."

def test_pipeline_overview_describes_phases():
    """Test that pipeline overview describes all phases."""
    overview = DOCS_DIR / "pipeline_overview.md"
    content = overview.read_text()
    assert "Phase 1" in content, "Overview must describe Phase 1."
    assert "Phase 2" in content, "Overview must describe Phase 2."
    assert "Phase 3" in content, "Overview must describe Phase 3."