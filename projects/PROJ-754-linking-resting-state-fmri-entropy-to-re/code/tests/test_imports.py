"""
Verify that every public module under ``code/src`` can be imported.
This satisfies the T001 requirement that the package layout is importable.
"""
import importlib
import pkgutil
import sys
from pathlib import Path

# Ensure the project root is on ``sys.path`` so that ``src`` alias works.
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def _iter_modules(package_name: str):
    """Yield fully‑qualified module names under ``package_name``."""
    pkg = importlib.import_module(package_name)
    for _, modname, ispkg in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):
        if not ispkg:
            yield modname

def test_all_modules_importable():
    """
    Import each module under ``src`` (the top‑level shim) and assert no
    ImportError is raised.
    """
    for module_name in _iter_modules("src"):
        importlib.import_module(module_name)