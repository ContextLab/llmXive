"""
Site customization module to ensure that the real NumPy package is used
throughout the project, even if a local module named ``numpy`` shadows the
external dependency. This file is automatically imported by Python at
interpreter start‑up if it is located on the import path (the project root
is added to ``sys.path`` by the test harness).
"""
import importlib
import sys
from types import ModuleType

def _load_real_numpy() -> ModuleType:
    """
    Load the genuine NumPy package from the environment, bypassing any
    project‑local ``numpy`` modules that might shadow it.
    """
    # Attempt to import the real NumPy using its spec from site‑packages.
    # ``importlib.import_module`` would resolve to the first matching name on
    # ``sys.path`` which could be the local stub; therefore we locate the
    # spec manually and load it.
    spec = importlib.util.find_spec("numpy")
    if spec is None or spec.origin is None:
        raise ImportError("Unable to locate the real NumPy installation.")

    # If the spec points to this project (i.e., a stub), fall back to the
    # package installed in ``site‑packages`` by re‑searching with ``pip``'s
    # metadata. The simplest reliable approach is to import the helper
    # module ``numpy_real`` which imports NumPy using an absolute import.
    try:
        from .numpy_real import _real_numpy  # type: ignore
        return _real_numpy
    except Exception as exc:
        raise ImportError("Failed to import the real NumPy via numpy_real.") from exc

try:
    import numpy as _np  # noqa: F401
    # If the imported module lacks the expected attributes, replace it.
    if not hasattr(_np, "__version__"):
        real_np = _load_real_numpy()
        sys.modules["numpy"] = real_np
except Exception:
    # In the unlikely event that ``import numpy`` itself raises, ensure the
    # real implementation is loaded.
    sys.modules["numpy"] = _load_real_numpy()
