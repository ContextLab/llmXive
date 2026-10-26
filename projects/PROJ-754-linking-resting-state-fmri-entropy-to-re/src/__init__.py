"""
src package initializer
-----------------------
This file ensures that the project's source code located in
``code/src`` is importable as the top‑level ``src`` package.
By inserting the absolute path of ``code/src`` at the front of
``sys.path`` we make modules such as ``src.stats.power_pre`` work
without moving any existing files.
"""
import sys
from pathlib import Path

# Resolve the project root (the directory that contains the ``code`` folder)
_project_root = Path(__file__).resolve().parent
_code_src_path = _project_root / "code" / "src"

# Insert the path if it's not already present
if str(_code_src_path) not in sys.path:
    sys.path.insert(0, str(_code_src_path))
