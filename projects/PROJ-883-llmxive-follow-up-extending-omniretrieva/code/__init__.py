"""
Package initialization for the project.

This file ensures that the top‑level imports such as
``import generators.synthetic_query`` work correctly by adding the
``code`` directory to ``sys.path``.  All packages that live under
``code/`` (e.g., ``code/generators``) become importable as top‑level
packages (``generators``, ``executors``, etc.).
"""
import sys
from pathlib import Path

# Add the ``code`` directory to the import search path so that
# statements like ``import generators.synthetic_query`` resolve to
# ``code/generators``.
CODE_ROOT = Path(__file__).parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))
