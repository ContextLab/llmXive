"""
Project‑wide ``sitecustomize`` to ensure the genuine NumPy package is used.

The repository contains a ``code/numpy`` package that unintentionally shadows
the real NumPy installation from the environment. Importing NumPy (or any
library that depends on it, such as pandas or scipy) would otherwise import
this stub package, leading to attribute errors like ``module 'numpy' has no
attribute '__version__'``.

By loading the real NumPy from the site‑packages directory *before* any
other imports and registering it under ``sys.modules['numpy']``, we guarantee
that all subsequent imports receive the correct implementation.
"""
import importlib.util
import sys
import sysconfig

def _load_real_numpy():
    """Load the actual NumPy distribution from site‑packages."""
    site_pkgs = sysconfig.get_paths()["purelib"]
    spec = importlib.util.find_spec("numpy", [site_pkgs])
    if spec is None or spec.loader is None:
        raise ImportError("Real NumPy could not be located in site‑packages.")
    real_numpy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(real_numpy)
    sys.modules["numpy"] = real_numpy
    return real_numpy

# Execute at import time.
_load_real_numpy()