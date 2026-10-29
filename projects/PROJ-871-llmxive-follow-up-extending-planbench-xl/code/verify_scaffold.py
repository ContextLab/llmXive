"""
Verification and creation script for project scaffold.

This script ensures that the essential top‑level directories
``code/``, ``data/`` and ``tests/`` exist under the project root
(the directory containing this script's ``code`` folder). If any are
missing, they are created. The script exits with status 0 on success,
otherwise prints an error message to stderr and exits with status 1.
"""

import sys
from pathlib import Path

# Resolve the project root as the parent of the ``code`` directory
try:
    # ``paths.root`` may point to the repository root; we prefer the
    # directory two levels up from this file (i.e. the project root).
    from llmxive_toolkit import paths
    project_root = Path(__file__).resolve().parents[1]
except Exception:
    # Fallback: infer the root as the parent of the ``code`` folder.
    project_root = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = ("code", "data", "tests")

missing = []
for d in REQUIRED_DIRS:
    dir_path = project_root / d
    if not dir_path.is_dir():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            missing.append(f"{d} (failed to create: {e})")
        else:
            # Created successfully; continue.
            continue
    # Directory exists
    continue

# After attempted creation, recompute any still‑missing directories.
still_missing = [d for d in REQUIRED_DIRS if not (project_root / d).is_dir()]
if still_missing:
    sys.stderr.write(
        f"Missing required directories after creation attempt: {', '.join(still_missing)}\\n"
    )
    sys.exit(1)

print("All required directories exist.")
sys.exit(0)