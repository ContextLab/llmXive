import pytest
from pathlib import Path

# The module under test lives directly in the ``code`` package.
from setup_project_structure import create_directories


@pytest.fixture
def temp_project_root(tmp_path_factory):
    """
    Provide a temporary directory that mimics the repository root.
    The fixture yields the path and lets pytest clean it up automatically.
    """
    return tmp_path_factory.mktemp("temp_repo_root")


def test_create_directories_creates_all_paths(temp_project_root):
    """
    Verify that ``create_directories`` creates every required folder.
    """
    # Execute the directory‑creation logic using the temporary root.
    create_directories(temp_project_root)

    root = Path(temp_project_root) / "projects" / "PROJ-236-exploring-the-influence-of-network-topol"
    expected_dirs = [
        root / "code" / "utils",
        root / "code" / "tests" / "unit",
        root / "code" / "tests" / "integration",
        root / "data" / "raw",
        root / "data" / "networks",
        root / "data" / "transport",
        root / "data" / "analysis",
        root / "plots",
        root / "state" / "projects",
    ]

    for d in expected_dirs:
        assert d.is_dir(), f"Expected directory {d} to exist"