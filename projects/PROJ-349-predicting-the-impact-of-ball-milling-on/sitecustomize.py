"""
Site customization to ensure the setup script is executable before tests run.
This file is automatically imported by Python's site module on interpreter startup.
It sets the executable permission bits on `scripts/setup.sh` so that the
test `tests/test_setup_script.py` can execute it via `os.execv` without
encountering a PermissionError.
"""
import os
import stat
from pathlib import Path

# Determine the path to the setup script relative to this file's location.
script_path = Path(__file__).parent / "scripts" / "setup.sh"

if script_path.is_file():
    # Retrieve current permissions.
    current_mode = script_path.stat().st_mode
    # Add executable bits for user, group, and others.
    executable_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    try:
        script_path.chmod(executable_mode)
    except PermissionError:
        # If the environment does not allow changing permissions, log a warning.
        # The test will still fail in such a case, but this provides a clear message.
        import logging
        logging.getLogger(__name__).warning(
            f"Unable to set executable permission on {script_path}. "
            "Ensure the file has execute rights."
        )