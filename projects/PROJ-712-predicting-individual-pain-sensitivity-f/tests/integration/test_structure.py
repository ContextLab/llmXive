"""
Integration test for directory creation script.

This test runs the `scripts/create_dirs.sh` helper script and then
asserts that each of the required project directories exists.
"""

import subprocess
from pathlib import Path

def test_create_dirs():
    """
    Execute the directory‑creation script and verify that the expected
    directories are present afterwards.
    """
    # Resolve the project root (two levels up from this test file)
    project_root = Path(__file__).resolve().parents[2]

    # Path to the helper script
    script_path = project_root / "scripts" / "create_dirs.sh"

    # Run the script; it should exit with status 0
    subprocess.check_call(["bash", str(script_path)])

    # List of directories that must exist
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "artifacts",
        project_root / "state",
        project_root / "code",
        project_root / "tests",
    ]

    # Assert each directory exists
    for d in required_dirs:
        assert d.is_dir(), f"Required directory missing: {d}"
