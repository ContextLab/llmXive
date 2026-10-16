import subprocess
import sys
from pathlib import Path

import pytest

@pytest.fixture(scope="session")
def project_root():
    """Root directory of the repository (one level above this test file)."""
    return Path(__file__).resolve().parent.parent

def read_manifest_dirs(manifest_path: Path):
    """Parse the manifest and return a set of directory paths relative to the project root."""
    dirs = set()
    with manifest_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # If line ends with '/', it's a directory entry
            if line.endswith("/"):
                dirs.add(line.rstrip("/"))
    return dirs

def test_setup_script_creates_directories(project_root: Path):
    """
    Verify that `scripts/setup.sh` runs without error and creates all directories
    listed in `scripts/setup_manifest.txt`.
    """
    manifest_path = project_root / "scripts" / "setup_manifest.txt"
    setup_script = project_root / "scripts" / "setup.sh"

    # Ensure the script is executable (POSIX systems will still run it via the interpreter)
    assert setup_script.is_file(), "setup.sh does not exist"

    # Run the setup script
    result = subprocess.run(
        [sys.executable, "-c", "import os; os.execv('{}', ['{}'])".format(setup_script, setup_script)],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    # The script should exit with code 0
    assert result.returncode == 0, f"setup.sh failed: {result.stderr}"

    # Verify each directory from the manifest now exists
    expected_dirs = read_manifest_dirs(manifest_path)
    for rel_dir in expected_dirs:
        dir_path = project_root / rel_dir
        assert dir_path.is_dir(), f"Expected directory {dir_path} was not created"