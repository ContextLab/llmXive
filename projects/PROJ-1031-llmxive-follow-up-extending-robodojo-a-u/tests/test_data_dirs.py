"""
Unit test for the data directory creation script.

The test runs the script via its `main` function and then checks that the
required directories exist under the project root `data/` folder.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Import the script as a module without executing it on import.
script_path = Path(__file__).resolve().parents[1] / "scripts" / "create_data_dirs.py"
spec = importlib.util.spec_from_file_location("create_data_dirs", script_path)
module = importlib.util.module_from_spec(spec)
sys.modules["create_data_dirs"] = module
spec.loader.exec_module(module)  # type: ignore

def test_create_data_dirs():
    """Run the script and verify the directory hierarchy."""
    exit_code = module.main()
    assert exit_code == 0, "Script should exit with status 0"

    # Expected sub‑folders under the project root `data/`
    root_data = Path(__file__).resolve().parents[2] / "data"
    expected = {"raw", "interim", "processed", "final"}
    actual = {p.name for p in root_data.iterdir() if p.is_dir()}
    assert expected.issubset(actual), f"Missing directories: {expected - actual}"