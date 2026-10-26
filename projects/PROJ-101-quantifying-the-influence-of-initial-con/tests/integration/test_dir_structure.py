"""
Integration test for the directory layout and manifest creation.

This test ensures that:
  1. The `code.setup_dir_structure` module can be executed without error,
     creating all required top‑level directories under the project root.
  2. The manifest file `data/dir_structure.txt` exists and lists exactly the
     nine expected directories, one per line.
  3. (Optional) The external `tree` command, if available, can list the
     directory tree up to depth 2 without error.

The CI step described in the task specification runs `cat
data/dir_structure.txt` and asserts the presence of each directory name.
This pytest test provides the same verification in an automated manner.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Expected directory hierarchy (relative to project root)
EXPECTED_DIRS = [
    "code",
    "code/simulation",
    "code/analysis",
    "code/utils",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/processed",
    "data/processed/plots",
]


def test_setup_dir_structure_creates_all_directories_and_manifest(tmp_path):
    """
    Run the setup script, then verify that all directories exist and that the
    manifest file contains the exact expected entries.
    """
    # Execute the module as a script to (re)create the layout.
    # Using subprocess ensures the script runs in a fresh process, matching
    # the CI behaviour.
    result = subprocess.run(
        [sys.executable, "-m", "code.setup_dir_structure"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"setup_dir_structure failed: {result.stderr}"

    # Verify each expected directory exists.
    for rel_dir in EXPECTED_DIRS:
        dir_path = paths.path(*rel_dir.split("/"))
        assert dir_path.is_dir(), f"Expected directory missing: {dir_path}"

    # Verify the manifest file exists.
    manifest_path = paths.data("dir_structure.txt")
    assert manifest_path.is_file(), f"Manifest file not found at {manifest_path}"

    # Read manifest contents and compare line‑by‑line.
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest_lines = [line.strip() for line in f if line.strip()]

    # The manifest should contain exactly the expected directories, in any order.
    assert set(manifest_lines) == set(EXPECTED_DIRS), (
        "Manifest contents do not match expected directory list.\n"
        f"Expected: {EXPECTED_DIRS}\n"
        f"Found:    {manifest_lines}"
    )

    # Optional: if the `tree` command is available, run it to ensure it works.
    # The CI specification mentions `tree -L 2`; this block is defensive
    # and will simply skip the check if `tree` is not installed.
    try:
        tree_result = subprocess.run(
            ["tree", "-L", "2", str(paths.root)],
            capture_output=True,
            text=True,
            check=True,
        )
        # Basic sanity: the output should contain the top‑level directories.
        for top_dir in ["code", "tests", "data"]:
            assert top_dir in tree_result.stdout, f"tree output missing {top_dir}"
    except FileNotFoundError:
        # `tree` is not installed on the runner; this is acceptable.
        log.info("`tree` command not found; skipping tree verification.")
    except subprocess.CalledProcessError as e:
        # If `tree` exists but fails, surface the error.
        raise AssertionError(f"`tree` command failed: {e.stderr}") from e
    
    # If we reach this point, the layout and manifest are verified.
    log.info("Directory layout and manifest verification passed.")