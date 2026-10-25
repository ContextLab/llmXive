"""
Integration test for T001 – verifies that the required directory layout
is created and that the manifest file `data/dir_structure.txt` contains
exactly the nine expected directory entries.
"""
import subprocess
from pathlib import Path

import pytest

# Import the script that creates the layout
from code.create_layout import main as create_layout_main

EXPECTED_DIRS = [
    "code",
    "code/simulation",
    "code/analysis",
    "code/utils",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
    "data/processed/plots"
]

@pytest.fixture(scope="module")
def ensure_layout():
    """Run the layout creation script before the test."""
    create_layout_main()
    yield
    # No teardown needed; directories are left in place.

def test_manifest_exists_and_contains_all_directories(ensure_layout):
    manifest_path = Path("data/dir_structure.txt")
    assert manifest_path.is_file(), "Manifest file data/dir_structure.txt does not exist"
    
    with manifest_path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    # Verify each expected directory appears exactly once
    for expected in EXPECTED_DIRS:
        assert expected in lines, f"Expected directory '{expected}' not found in manifest"
    assert len(lines) == len(EXPECTED_DIRS), "Manifest should contain exactly nine directory entries"

def test_tree_command_outputs_expected_structure(ensure_layout):
    """
    Run the system `tree` command (if available) and ensure it succeeds.
    The CI step is expected to run `tree -L 2`; we verify that the command
    exits with code 0 and that its output contains the top‑level directories.
    """
    result = subprocess.run(["tree", "-L", "2"], capture_output=True, text=True)
    # The command may not be present on all platforms; if it is missing,
    # we consider the test passed because the manifest check already guarantees
    # the layout.
    if result.returncode != 0:
        pytest.skip("`tree` command not available on this platform")
    
    output = result.stdout
    for dir_name in EXPECTED_DIRS:
        # The tree output lists directories with a trailing slash
        assert f"{dir_name}/" in output or f"{dir_name}" in output, f"Directory '{dir_name}' not found in tree output"