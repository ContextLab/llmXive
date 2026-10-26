"""
Top‑level ``src`` package shim.

The project stores its source code under ``code/src``.  To allow
test modules that import ``src.xxx`` (e.g. ``src.analysis.entropy``)
to resolve to the actual implementation, we extend this package’s
``__path__`` to include the sibling ``code/src`` directory.

This approach avoids duplication of the code tree while keeping the
import layout expected by the test suite.
"""
import os
from pathlib import Path

# Resolve the path to the real source directory ``code/src``.
_project_root = Path(__file__).resolve().parent.parent
_real_src_dir = _project_root / "code" / "src"

# If the directory exists, add it to the package search path.
if _real_src_dir.is_dir():
    __path__.append(str(_real_src_dir))
