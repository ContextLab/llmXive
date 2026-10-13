"""
Unit test for the project‑initialization script.

The test simply verifies that the expected directories exist after the
`create_project_structure.py` script has been run.  Because the script
is idempotent, the test can be executed repeatedly without side effects.
"""

import pathlib

from llmxive_toolkit import paths

def test_directories_exist():
    """Assert that all required top‑level directories are present."""
    required_dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("processed"),
        paths.results(),
        paths.tests("unit"),
        paths.tests("contract")
    ]

    missing = [str(p) for p in required_dirs if not p.is_dir()]
    assert not missing, f"Missing expected directories: {', '.join(missing)}"