"""
Test that the core directory creation script successfully creates the required
directories under the project root.
"""
import os
import subprocess
import sys

def test_core_directories_created():
    """
    Execute the directory creation script and verify that each required
    directory now exists on disk.
    """
    # Run the script
    result = subprocess.run(
        [sys.executable, "code/create_core_dirs.py"],
        capture_output=True,
        text=True,
    )
    # The script should exit cleanly
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify each directory exists
    required_dirs = [
        os.path.join("data", "raw"),
        os.path.join("data", "processed"),
        os.path.join("data", "primes"),
        os.path.join("data", "targets"),
    ]
    for d in required_dirs:
        assert os.path.isdir(d), f"Expected directory {d} does not exist"

    # Optionally, check that the script printed expected messages
    for d in required_dirs:
        assert f"Ensured directory exists: {d}" in result.stdout, f"Missing output for {d}"