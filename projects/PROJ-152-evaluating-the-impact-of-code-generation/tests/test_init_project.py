"""
test_init_project.py

Integration test that runs the init_project script and verifies that the expected
directories have been created.
"""

import subprocess
import sys
from pathlib import Path

def test_project_structure_created(tmp_path, monkeypatch):
    """
    Run the init_project script and check that the required directories exist.
    """
    # Determine the repository root relative to this test file
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "code" / "init_project.py"

    # Execute the script
    result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expected project root
    project_root = repo_root / "projects" / "PROJ-152-evaluating-the-impact-of-code-generation"

    # Verify each subdirectory exists
    for sub in ["code", "data", "tests", "docs"]:
        assert (project_root / sub).is_dir(), f"Missing directory: {project_root / sub}"