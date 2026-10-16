"""
Site customization module to ensure the setup script is executable before tests run.
This file is automatically imported by Python's site initialization if present on
the import path (the project root is added to sys.path by the test runner).
It sets the executable bit on `scripts/setup.sh` so that the test invoking
`os.execv` can run the script without a PermissionError.
"""
import os
import stat
from pathlib import Path

# Path to the setup script relative to this file's location (project root)
setup_script_path = Path(__file__).resolve().parent / "scripts" / "setup.sh"

if setup_script_path.is_file():
    # Retrieve current permissions and add execute bits for user, group, others
    current_mode = setup_script_path.stat().st_mode
    exec_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    try:
        setup_script_path.chmod(exec_mode)
    except PermissionError:
        # In environments where the file system is read‑only, we cannot set the mode.
        # The test will then fail, indicating a configuration issue.
        pass
else:
    # If the script does not exist, we raise an error to surface the problem early.
    raise FileNotFoundError(f"Expected setup script not found at {setup_script_path}")