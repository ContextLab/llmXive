"""
Unit tests for project initialization (T001a).
Verifies that the required directories exist and are writable.
"""

import pytest
from pathlib import Path
from llmxive_toolkit import paths
from code.initialize_project import main as init_main

def test_directories_exist_and_writable():
    """
    Runs the initialization script and checks each required directory.
    """
    # Run the initialization routine
    init_main()

    required_dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("processed"),
        paths.results(),
        paths.tests("unit"),
        paths.tests("contract"),
    ]

    for dir_path in required_dirs:
        # Existence check
        assert dir_path.exists(), f"Directory should exist: {dir_path}"
        # Writability check
        test_file = dir_path / ".tmp_writable"
        try:
            with open(test_file, "w") as f:
                f.write("ok")
            test_file.unlink()
        except Exception as e:
            pytest.fail(f"Directory not writable {dir_path}: {e}")