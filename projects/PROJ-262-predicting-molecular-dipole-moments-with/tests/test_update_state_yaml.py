"""Test that ``code.update_state_yaml`` creates a non‑empty state YAML file."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Import the module under test
from code.update_state_yaml import main as update_state_main

@pytest.fixture
def state_file_path(tmp_path: Path) -> Path:
    """Return the expected location of the state file inside the temporary project root."""
    # The test runs from the repository root, so we mimic the repository layout.
    # The script itself computes the path relative to its own location, so we just
    # ensure the file is created where the script expects it.
    return Path(__file__).resolve().parents[2] / "state" / "projects" / "001-predicting-molecular-dipole-moments.yaml"

def test_state_yaml_is_created_and_nonempty(state_file_path: Path):
    # Ensure any stale file is removed before the test
    if state_file_path.is_file():
        state_file_path.unlink()

    # Run the script
    exit_code = update_state_main([])
    assert exit_code == 0, "Script should exit with code 0"

    # Verify the file now exists
    assert state_file_path.is_file(), f"Expected state file at {state_file_path}"

    # Verify the file is not empty and looks like YAML
    content = state_file_path.read_text(encoding="utf-8")
    assert content.strip().startswith("files:"), "YAML should start with a top‑level 'files:' key"
    assert len(content.strip()) > 10, "YAML content should be non‑trivial"

    # Basic sanity check: at least one entry should be present (the test file itself)
    assert "- path:" in content, "YAML should contain at least one file entry"
