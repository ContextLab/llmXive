"""
Top-level src package initializer.

This file ensures that the project's internal modules located under
``code/src`` are importable via the ``src`` namespace, which is required
by the existing test suite and other source files (e.g. ``src.qc``,
``src.utils``). By inserting the absolute path of ``code/src`` into
``sys.path`` at import time we make those modules discoverable without
altering the original package layout.
"""
import os
import sys
from pathlib import Path

# Resolve the directory that contains the project's ``code/src`` package.
_project_root = Path(__file__).resolve().parent
_code_src_dir = _project_root.parent / "code" / "src"

# Insert ``code/src`` at the front of ``sys.path`` if not already present.
if str(_code_src_dir) not in sys.path:
    sys.path.insert(0, str(_code_src_dir))

# Export a clean namespace.
__all__ = []
