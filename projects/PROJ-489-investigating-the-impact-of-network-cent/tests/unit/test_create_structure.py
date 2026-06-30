"""Test that the ``create_structure.py`` script creates the required directories."""

import subprocess
import sys
from pathlib import Path

def test_create_structure():
    # Resolve the repository root (two levels up from this test file)
    repo_root = Path(__file__).resolve().parents[2]

    # Path to the script we want to test
    script_path = repo_root / "code" / "create_structure.py"

    # Execute the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )

    # The script should exit cleanly
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"

    # Verify that each expected directory now exists
    expected_dirs = [
        repo_root / "code",
        repo_root / "data" / "raw",
        repo_root / "data" / "processed",
        repo_root / "data" / "metrics",
        repo_root / "data" / "results",
        repo_root / "tests" / "unit",
        repo_root / "tests" / "integration",
    ]

    for d in expected_dirs:
        assert d.is_dir(), f"Required directory not found: {d}"