"""
Unit test for the directory-structure setup script.

It runs ``code/setup_structure.py`` and checks that the generated
``data/results/structure_manifest.txt`` contains at least 11 lines,
as required by task T001.
"""

import subprocess
from pathlib import Path

def test_structure_manifest():
    # Execute the setup script.
    result = subprocess.run(
        [sys.executable, "code/setup_structure.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    manifest_path = Path("data/results/structure_manifest.txt")
    assert manifest_path.is_file(), "Manifest file was not created"

    # Verify the manifest contains at least 11 directory entries.
    with manifest_path.open() as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) >= 11, f"Manifest has {len(lines)} lines, expected >= 11"