"""
Unit test for the create_directories script (task T001).

The test imports the public `create_directories` function, invokes it,
and then asserts that every required directory exists.
"""

import os
from pathlib import Path

# Import the function from the sibling module.
from create_directories import create_directories

def test_create_directories_creates_all_paths(tmp_path):
    """
    Ensure that `create_directories` creates the full hierarchy required by
    task T001. The test runs in a temporary directory to avoid interfering
    with the actual repository layout.
    """
    # Temporarily change the working directory to the temporary path.
    original_cwd = Path.cwd()
    os.chdir(tmp_path)

    try:
        # Run the directory creation logic.
        create_directories()

        # Build the expected paths relative to the temporary directory.
        base = Path(tmp_path) / "projects" / "PROJ-546-predicting-molecular-properties-from-qua"
        expected = [
            base,
            base / "code",
            base / "data" / "raw",
            base / "data" / "optimized_geometries",
            base / "logs",
            base / "reports",
            base / "specs" / "546-predicting-molecular-properties" / "contracts",
            base / "tests" / "unit",
            base / "tests" / "integration",
            base / "tests" / "contract",
        ]

        missing = [str(p) for p in expected if not p.is_dir()]
        assert not missing, f"The following required directories were not created: {missing}"
    finally:
        # Restore original working directory.
        os.chdir(original_cwd)