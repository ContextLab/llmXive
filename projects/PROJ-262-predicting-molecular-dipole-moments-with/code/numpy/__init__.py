"""
Proxy module for the real NumPy package.

The project contains a placeholder ``code/numpy`` package that shadows the
genuine NumPy installation from the environment.  This proxy imports the
actual NumPy distribution (via ``code/numpy_real.py``) and re‑exports all
of its public attributes so that downstream libraries such as pandas and
SciPy can access ``numpy.__version__`` and the full NumPy API.
"""
import importlib
import sys
from types import ModuleType

# Import the helper that loads the real NumPy implementation.
# ``numpy_real.py`` simply does ``import numpy as _real_numpy`` which
# resolves to the genuine NumPy package installed in the environment.
_helper = importlib.import_module('numpy_real')
_real_numpy = getattr(_helper, '_real_numpy', None)

if _real_numpy is None:
    # Fallback – try to import NumPy directly (may recurse to this stub,
    # but in practice the helper always succeeds).
    import numpy as _real_numpy

# Replace this module's dictionary with the real NumPy's dictionary.
# This makes ``import numpy as np`` behave exactly like the real package.
globals().update(_real_numpy.__dict__)

# Ensure the ``__version__`` attribute exists (required by pandas/ SciPy).
__version__ = getattr(_real_numpy, '__version__', '0.0.0')

# Keep a reference to the real module so that ``sys.modules['numpy']``
# points to this proxy (which now mirrors the real implementation).
sys.modules[__name__] = sys.modules[__name__]
