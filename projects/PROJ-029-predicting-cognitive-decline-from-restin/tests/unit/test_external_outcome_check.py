"""Tests for the external outcome check script (T025).

The test creates a minimal repository layout without any MCI conversion
files and then runs the script. It verifies that the limitation note is
written to the expected location.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Path to the script relative to the repository root
SCRIPT_PATH = Path(__file__).resolve().parents[2] / "code" / "11_external_outcome_check.py"

@pytest.fixture
def clean_artifacts(tmp_path_factory):
    """Ensure a clean `data/artifacts` directory for the test."""
    # Use the real repository `data` directory (not a temporary one) because the script
    # resolves paths relative to the project root.
    repo_root = Path(__file__).resolve().parents[2]
    artifacts_dir = repo_root / "data" / "artifacts"
    # Remove any pre‑existing limitation note to avoid false positives.
    note_path = artifacts_dir / "limitations.txt"
    if note_path.is_file():
        note_path.unlink()
    yield
    # Cleanup after test
    if note_path.is_file():
        note_path.unlink()

def test_limitation_note_written_when_mci_missing(clean_artifacts):
    """Run the script and assert that the limitation note is created."""
    repo_root = Path(__file__).resolve().parents[2]

    # Ensure the raw dataset directory exists but contains no MCI files.
    raw_dir = repo_root / "data" / "raw" / "ds000246"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Remove any participants.tsv that might exist from previous runs.
    participants_tsv = raw_dir / "participants.tsv"
    if participants_tsv.is_file():
        participants_tsv.unlink()

    # Execute the script in a subprocess to emulate the quick‑start execution.
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # The script should exit with status 0.
    assert result.returncode == 0, f"Script exited with {result.returncode}: {result.stderr}"

    # Verify that the limitation note was written.
    note_path = repo_root / "data" / "artifacts" / "limitations.txt"
    assert note_path.is_file(), "limitations.txt was not created"

    # Basic sanity check on the note content.
    content = note_path.read_text(encoding="utf-8")
    assert "Limitation: The dataset does not contain MCI conversion data" in content

# The test suite can be run with `pytest -q`.