"""
Tests for T010: Amendment to Principle VII (Static Analysis Tools).
Verifies the existence of the amendment document and state updates.
"""
import os
import yaml
from pathlib import Path
import pytest

# Project root relative to tests
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-488-evaluating-the-impact-of-code-generation.yaml"
AMENDMENT_DOC = DOCS_DIR / "amendment-vii.md"

def test_t010_amendment_document_exists():
    """
    T010 requires the creation of docs/amendment-vii.md.
    """
    assert AMENDMENT_DOC.exists(), "Amendment document docs/amendment-vii.md does not exist."
    
    content = AMENDMENT_DOC.read_text()
    assert "Principle VII" in content, "Amendment document must reference Principle VII."
    assert "radon" in content, "Amendment document must mention radon."
    assert "pylint" in content, "Amendment document must mention pylint."
    assert "CPU-tractable" in content, "Amendment document must include CPU feasibility argument."
    assert "≤6h" in content or "6 hours" in content, "Amendment document must reference the 6-hour runtime constraint."

def test_t010_state_update():
    """
    Verify that the state file reflects the drafted status of T010.
    """
    if not STATE_FILE.exists():
        pytest.skip("State file not yet created by the pipeline.")
    
    with open(STATE_FILE, "r") as f:
        state = yaml.safe_load(f)
    
    assert "amendment_status" in state, "State file missing 'amendment_status' key."
    assert "T010" in state["amendment_status"], "State file missing T010 entry."
    
    t010_status = state["amendment_status"]["T010"]
    assert t010_status.get("status") in ["drafted", "submitted", "approved"], \
        f"T010 status must be drafted/submitted/approved, found: {t010_status.get('status')}"
    
    assert t010_status.get("document_path") == "docs/amendment-vii.md", \
        "T010 document path in state file is incorrect."

def test_t010_content_validity():
    """
    Check that the amendment content contains the specific proposed text.
    """
    content = AMENDMENT_DOC.read_text()
    # Check for the core proposed text
    assert "Allow CPU-tractable static analysis tools (radon, pylint)" in content, \
        "Missing core proposed text in amendment."
    assert "documented justification" in content, \
        "Missing requirement for documented justification."
    assert "lightweight LLM inference exceeds runtime constraints" in content, \
        "Missing context about LLM inference constraints."