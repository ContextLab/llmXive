"""
src package initializer.

This file ensures that the project's internal source code located under
`code/src` is discoverable when importing `src.*` modules. By inserting the
absolute path of `code/src` into `sys.path`, Python can resolve imports such
as `src.config`, `src.data.download`, etc., without needing to duplicate
the source files.
"""
import sys
from pathlib import Path

# Resolve the absolute path to the `code/src` directory (two levels up from this file)
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_CODE_SRC_PATH = _PROJECT_ROOT / "code" / "src"

# Insert the path at the front of sys.path if it's not already present
if str(_CODE_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_CODE_SRC_PATH))
