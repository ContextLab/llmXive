"""
Shim to ensure that importing ``numpy`` resolves to the real NumPy package
installed in the environment.

The original project introduced a placeholder ``numpy`` package that attempted
to load a ``numpy_real`` module, which was missing and caused import errors.
This shim provides a robust implementation that directly imports the genuine
NumPy library and re‑exports its public symbols.
"""
import importlib
import sys

# Attempt to import the real NumPy library from the environment.
# If a module named ``numpy_real`` exists (e.g., a shim placed at the project
# root), use it; otherwise fall back to the standard NumPy import.
try:
    _real_numpy = importlib.import_module("numpy_real")
except Exception:
    # Import the actual NumPy package. The import machinery will locate the
    # distribution installed in the environment (e.g., site‑packages).
    _real_numpy = importlib.import_module("numpy")

# Populate the current module's globals with everything from the real NumPy.
globals().update(_real_numpy.__dict__)

# Ensure that ``sys.modules['numpy']`` points to this shim (already the case)
# and that ``sys.modules['numpy_real']`` also references the real NumPy module
# for any downstream imports.
sys.modules.setdefault("numpy_real", _real_numpy)
