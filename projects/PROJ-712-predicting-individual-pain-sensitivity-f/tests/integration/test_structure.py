"""
Integration test for directory creation script (task T001).

Runs `scripts/create_dirs.sh` and asserts that each of the SIX
required project directories exists afterwards:
data/raw, data/processed, artifacts, code, tests, scripts.
"""

import subprocess
from pathlib import Path


def test_create_dirs():
    """
    Execute the directory-creation script and verify that the expected
    directories are present afterwards.
    """
    # Resolve the project root:
    # tests/integration/test_structure.py -> parents[0]=integration, [1]=tests, [2]=root
    project_root = Path(__file__).resolve().parents[2]

    script_path = project_root / "scripts" / "create_dirs.sh"
    assert script_path.is_file(), f"Helper script missing: {script_path}"

    # Run the script; it should exit with status 0
    subprocess.check_call(["bash", str(script_path)])

    # All six directories required by task T001 must exist.
    # 'state/' is excluded as it is platform-owned.
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "artifacts",
        project_root / "code",
        project_root / "tests",
        project_root / "scripts",
    ]

    for d in required_dirs:
        assert d.is_dir(), f"Required directory missing: {d}"