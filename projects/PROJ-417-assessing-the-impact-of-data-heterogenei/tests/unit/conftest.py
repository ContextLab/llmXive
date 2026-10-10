"""
Pytest configuration for the unit test suite.

Ensures the ``code/`` directory is on ``sys.path`` so that the
project packages (``simulation``, ``analysis``, ``utils``,
``config_loader``) are importable from the tests, regardless of
where pytest is invoked from. This fixes the T002 rejection where
``import simulation.generator`` failed because no importable
top-level ``simulation`` package was resolvable.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"

for p in (str(CODE_DIR), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
