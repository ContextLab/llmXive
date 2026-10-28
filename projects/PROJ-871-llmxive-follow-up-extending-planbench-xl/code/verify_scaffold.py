"""
Verification script for project scaffold.

This script checks that the essential top‑level directories
``code/``, ``data/`` and ``tests/`` exist under the project root.
It exits with status 0 if all are present, otherwise prints an
error message to stderr and exits with status 1.
"""

import sys
from pathlib import Path

# ``paths.root`` resolves to the project root directory.
# Using the toolkit ensures we honour any custom project layout.
try:
    from llmxive_toolkit import paths
    project_root = paths.root
except Exception:
    # Fallback: infer the root as two levels up from this file.
    project_root = Path(__file__).resolve().parents[2]

REQUIRED_DIRS = ("code", "data", "tests")

missing = [d for d in REQUIRED_DIRS if not (project_root / d).is_dir()]

if missing:
    sys.stderr.write(f"Missing required directories: {', '.join(missing)}\\n")
    sys.exit(1)

print("All required directories exist.")
sys.exit(0)