"""
test_setup_structure.py

Integration test for the `code/setup_structure.py` script.
It executes the script and then verifies that all required directories
exist on the filesystem.
"""

import importlib.util
import sys
from pathlib import Path

def _load_and_run_script(script_path: Path):
    """
    Dynamically load the script as a module and invoke its `main` function.
    """
    spec = importlib.util.spec_from_file_location("setup_structure", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    # The script defines a `main` function that returns an exit code.
    exit_code = module.main()
    assert exit_code == 0, f"setup_structure exited with code {exit_code}"

def test_project_directories_created():
    """
    Run the setup_structure script and assert that each expected directory now exists.
    """
    # Resolve the path to the script relative to this test file
    script_path = Path(__file__).resolve().parents[1] / "code" / "setup_structure.py"
    assert script_path.is_file(), f"Script not found at {script_path}"

    # Execute the script
    _load_and_run_script(script_path)

    # Determine the project root (two levels up from the test file)
    project_root = Path(__file__).resolve().parents[2]

    # List of directories that must exist after the script runs
    expected_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "logs",
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "utils",
        project_root / "artifacts" / "models",
        project_root / "artifacts" / "figures",
        project_root / "artifacts" / "reports",
        project_root / "tests",
        project_root / "docs",
    ]

    for d in expected_dirs:
        assert d.is_dir(), f"Expected directory missing: {d}"