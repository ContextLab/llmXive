import os
import pytest

def test_directory_structure():
    """
    Verify that all required project directories exist.
    This test asserts os.path.isdir() for the 12 specific directories
    listed in the task description for T001a.
    """
    # Define the root of the project (assuming tests/unit/ is 3 levels deep from root)
    # The task specifies paths relative to the project root.
    # We assume the current working directory or the script location allows us to reach root.
    # Since the test is in tests/unit/, we go up 3 levels to get to the root where src/, data/ etc reside.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

    required_dirs = [
        "src",
        "tests",
        "data",
        "contracts",
        "state",
        "logs",
        "templates",
        "data/raw",
        "data/processed",
        "data/samples",
        "src/gatekeeper",
        "src/utils",
        "src/cli",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]

    missing_dirs = []
    for dir_name in required_dirs:
        full_path = os.path.join(project_root, dir_name)
        if not os.path.isdir(full_path):
            missing_dirs.append(dir_name)

    assert len(missing_dirs) == 0, f"The following required directories are missing: {missing_dirs}"