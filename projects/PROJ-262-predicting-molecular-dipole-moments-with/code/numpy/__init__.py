"""
Shim package for ``numpy`` that forwards all attributes to the real NumPy
installation found in the environment's ``site-packages`` directory.

The project contains a top‑level ``code/numpy`` package which would normally
shadow the genuine NumPy library, causing import errors (e.g. missing
``__version__``) in downstream libraries such as pandas and scipy.

This shim locates the external NumPy distribution on the ``PYTHONPATH``,
loads it explicitly, and re‑exports its public API so that any ``import
numpy`` statement receives the fully‑functional library.
"""

import importlib.util
import sys
from types import ModuleType

def _load_external_numpy() -> ModuleType:
    """
    Load the real NumPy package from a ``site-packages`` directory,
    bypassing the local ``code/numpy`` package that would otherwise be
    imported.
    
    Returns:
        The external NumPy module.
    
    Raises:
        ImportError: If no external NumPy distribution can be found.
    """
    # Scan sys.path for entries that look like a site‑packages directory.
    # This heuristic works for typical virtual‑environment layouts.
    for path_entry in sys.path:
        if not path_entry:  # skip empty entry which represents cwd
            continue
        if "site-packages" not in path_entry:
            continue
        # Attempt to find a ``numpy`` spec inside this entry only.
        spec = importlib.util.find_spec("numpy", [path_entry])
        if spec and spec.origin and "site-packages" in spec.origin:
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None  # for mypy / linters
            spec.loader.exec_module(module)
            return module
    raise ImportError(
        "Unable to locate external NumPy installation in any site‑packages path."
    )

# Load the genuine NumPy once and expose it under the current package name.
_real_numpy = _load_external_numpy()

# Re‑export everything that the real NumPy provides. This mimics the behaviour
# of a normal import, making ``import numpy`` indistinguishable from the real
# library for downstream code.
globals().update(_real_numpy.__dict__)

# Ensure that subsequent ``import numpy`` statements receive this shim module.
sys.modules[__name__] = _real_numpy