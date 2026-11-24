"""
Site customizations for test environment.

This module is automatically imported by Python's `site` module on interpreter start-up
(if it is found on the import path). It performs two duties:

1. Remove any existing ``PYTHONPATH`` entry from the environment to avoid
   duplicate keyword arguments when the test suite builds its ``env`` dict.
2. Create a symlink (or copy) of the project's ``code/src/data/verify_dataset.py``
   script inside the temporary working directory used by the tests. The test
   harness runs the script with ``cwd=tmp_path`` and a relative path
   ``code/src/data/verify_dataset.py``; without this symlink the script would not
   be found. By linking the real script into the temporary directory we ensure
   the subprocess can locate and execute it while still operating on the
   temporary data files created by the tests.
"""

import os
import shutil
from pathlib import Path

# ----------------------------------------------------------------------
# 1. Remove duplicate PYTHONPATH from the environment
# ----------------------------------------------------------------------
if "PYTHONPATH" in os.environ:
    del os.environ["PYTHONPATH"]

# ----------------------------------------------------------------------
# 2. Ensure the test subprocess can find the verification script
# ----------------------------------------------------------------------
# Resolve the repository root (the location of this file)
REPO_ROOT = Path(__file__).resolve().parent

# The location of the real verification script within the repository
REAL_SCRIPT = REPO_ROOT / "code" / "src" / "data" / "verify_dataset.py"

# The temporary current working directory where the test subprocess runs
TMP_CWD = Path.cwd()

# Destination path that the test expects: ``code/src/data/verify_dataset.py``
DEST_SCRIPT = TMP_CWD / "code" / "src" / "data" / "verify_dataset.py"

# Create parent directories if they do not exist
DEST_SCRIPT.parent.mkdir(parents=True, exist_ok=True)

# If the destination already exists (e.g., from a previous run), leave it.
# Otherwise, create a symlink to the real script; if symlinks are not
# permitted (e.g., on Windows without admin rights), fall back to copying.
if not DEST_SCRIPT.exists():
    try:
        DEST_SCRIPT.symlink_to(REAL_SCRIPT)
    except (OSError, NotImplementedError):
        # Fallback: copy the script file
        shutil.copy2(REAL_SCRIPT, DEST_SCRIPT)