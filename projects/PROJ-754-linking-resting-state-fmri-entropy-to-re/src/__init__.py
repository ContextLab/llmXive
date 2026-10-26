"""
src package initializer.
This adds the project's ``code/src`` directory to ``sys.path`` so that
imports such as ``import src.stats.power_pre`` resolve to the actual
implementation located under ``code/src``.
"""
import sys
from pathlib import Path

# Determine the absolute path to the ``code/src`` directory relative to this file.
_project_root = Path(__file__).resolve().parent
_code_src_path = _project_root / "code" / "src"

# Insert it at the front of ``sys.path`` if not already present.
if str(_code_src_path) not in sys.path:
    sys.path.insert(0, str(_code_src_path))
