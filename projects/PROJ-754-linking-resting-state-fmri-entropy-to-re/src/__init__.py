"""
src package initializer.
This file ensures that the project's internal `code/src` directory is added to
Python's module search path, allowing imports such as `import src.analysis.entropy`
to resolve to the implementation located under `code/src/`.
"""
import sys
from pathlib import Path

# Resolve the path to the internal source directory (project_root/code/src)
_project_root = Path(__file__).resolve().parent
_internal_src = _project_root / "code" / "src"

if _internal_src.is_dir():
    # Insert at the front of sys.path so it takes precedence
    sys.path.insert(0, str(_internal_src))
