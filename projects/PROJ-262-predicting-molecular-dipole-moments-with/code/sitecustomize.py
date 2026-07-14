"""
Site customization to ensure that the real NumPy package is used throughout the
project.

The repository contains a lightweight stub package named ``code/numpy`` which
shadows the actual NumPy installation.  This stub does not expose the full
NumPy API (e.g. ``__version__``) and causes import errors in third‑party
libraries such as pandas, scipy, and torch that rely on the real package.

To resolve this, we intercept the import of ``numpy`` at interpreter start‑up
(the ``sitecustomize`` module is imported automatically by Python if it is
found on the import path) and replace the stub with the genuine NumPy module
provided by the environment.

The real NumPy implementation is made available via the helper module
``code/numpy_real.py`` which simply imports the external ``numpy`` package.
By inserting that module into ``sys.modules`` under the name ``numpy`` we
guarantee that any subsequent ``import numpy as np`` statements resolve to the
full‑featured library.
"""

import importlib
import sys

# Import the helper that loads the genuine NumPy package.
# ``numpy_real`` lives at the repository root (i.e. ``code/numpy_real.py``) and
# imports the external ``numpy`` distribution as ``_real_numpy``.
_real_numpy = importlib.import_module("numpy_real")

# If the stub package has already been imported, replace it with the real one.
# ``setdefault`` ensures we do not overwrite an existing correct entry.
sys.modules.setdefault("numpy", _real_numpy)

# Additionally expose the real NumPy module under the name ``numpy`` for any
# code that may have performed a partial import (e.g. ``from numpy import ...``)
# before this point.
sys.modules["numpy"] = _real_numpy

# Clean up the temporary variable to avoid leaking it into the global namespace.
del _real_numpy
# The module does not define any public symbols; its side‑effect is sufficient.