"""Ensure the project's ``code/`` directory is importable when running pytest
from the repository root (e.g. ``pytest tests/unit/``)."""
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
