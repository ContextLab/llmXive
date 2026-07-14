"""
Proxy module that forwards attribute access to the real ``numpy`` package
installed in the environment.

A stray ``numpy`` package in the repository shadowed the genuine library,
causing import errors (e.g. missing ``__version__``). This shim restores the
expected behaviour without altering external dependencies.
"""
import importlib
import importlib.metadata
import sys
from types import ModuleType
from typing import Any

def _load_real_numpy() -> ModuleType:
    """
    Load the genuine NumPy distribution from the environment and return it
    as a module object. Raises ImportError if the distribution cannot be found.
    """
    try:
        # Locate the installed distribution (not the local ``numpy`` folder)
        dist = importlib.metadata.distribution("numpy")
        real_init = dist.locate_file("numpy/__init__.py")
    except importlib.metadata.PackageNotFoundError as exc:
        raise ImportError("NumPy is not installed in the environment.") from exc

    spec = importlib.util.spec_from_file_location("numpy_real", real_init)
    real_mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader  # for mypy
    spec.loader.exec_module(real_mod)  # type: ignore[assignment]
    return real_mod

# Load the genuine NumPy once and expose its public API.
_real_numpy = _load_real_numpy()
__version__ = getattr(_real_numpy, "__version__", "0.0.0")

def __getattr__(name: str) -> Any:
    """Delegate attribute access to the real NumPy module."""
    return getattr(_real_numpy, name)

def __dir__() -> list[str]:
    return sorted(set(dir(_real_numpy) + ["__version__"]))
