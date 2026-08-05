"""
T001a: Integration test asserting expected directories exist after execution.

This test verifies that the project layout created by `setup_project_layout.py`
matches the specification in `plan.md` and `tasks.md`.

Expected directories:
- src/
- tests/
- data/
- results/
- contracts/
- docs/
- .github/workflows/
"""

import os
from pathlib import Path

import pytest


# Define the expected directories relative to the project root
EXPECTED_DIRS = [
    "src",
    "tests",
    "data",
    "results",
    "contracts",
    "docs",
    ".github/workflows",
]


@pytest.fixture(scope="module")
def project_root() -> Path:
    """
    Locate the project root directory.

    Searches upwards from the test file location for 'tasks.md'.
    """
    current = Path(__file__).resolve()
    # Navigate up to the 'tests/integration' directory
    project_root = current.parent.parent

    # Fallback check: ensure tasks.md exists to confirm root
    if not (project_root / "tasks.md").exists():
        # Try going up one more level if we are deep in a nested structure
        potential_root = project_root.parent
        if (potential_root / "tasks.md").exists():
            project_root = potential_root
        else:
            # If still not found, assume current working directory is root
            project_root = Path.cwd()

    return project_root


def test_project_directory_layout_exists(project_root: Path) -> None:
    """
    Assert that all required project directories exist.

    This test fails if any of the expected directories are missing,
    indicating that T001 (setup_project_layout.py) has not been run
    or did not complete successfully.
    """
    missing_dirs = []

    for dir_name in EXPECTED_DIRS:
        target_path = project_root / dir_name
        if not target_path.exists():
            missing_dirs.append(dir_name)
        elif not target_path.is_dir():
            raise AssertionError(
                f"Path exists but is not a directory: {target_path}"
            )

    assert not missing_dirs, (
        f"The following required directories are missing: {missing_dirs}. "
        "Please run 'python code/setup_project_layout.py' to initialize the project layout."
    )

def test_project_root_has_tasks_md(project_root: Path) -> None:
    """
    Sanity check that we are in the correct project root by verifying tasks.md exists.
    """
    assert (project_root / "tasks.md").exists(), (
        f"Could not locate tasks.md in {project_root}. "
        "This test expects to be run from the project root or a subdirectory of it."
    )