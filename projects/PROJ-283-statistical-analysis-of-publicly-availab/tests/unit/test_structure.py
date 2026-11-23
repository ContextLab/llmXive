"""
Unit test for the ``create_directories`` script.

The test simply verifies that the expected directories exist after the
script has been executed. It does not attempt to recreate them – the
script is run as part of the test setup.
"""

import subprocess
from pathlib import Path

def test_directories_exist(tmp_path):
    """
    Run the ``setup_structure.py`` script and assert that all required
    directories are present in the project root.
    """
    # Resolve the path to the script relative to the repository root
    script_path = Path(__file__).resolve().parents[3] / "code" / "setup_structure.py"

    # Execute the script; it will create the directories
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0, f"Script exited with {result.returncode}: {result.stderr}"

    # Define the expected directories relative to the repository root
    project_root = script_path.parent.parent
    expected_dirs = [
        "src",
        "tests",
        "data",
        "specs",
        "data/raw",
        "data/processed",
        "data/results",
        "specs/contracts",
        "tests/contract",
        "tests/unit",
        "tests/integration",
    ]

    for rel_dir in expected_dirs:
        dir_path = project_root / rel_dir
        assert dir_path.is_dir(), f"Missing expected directory: {dir_path}"