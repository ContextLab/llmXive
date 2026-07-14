"""
Compatibility shim for the real NumPy library.

The project originally included a placeholder module named ``numpy_real`` that was
mistakenly shadowing the actual ``numpy`` package.  Several third‑party libraries
(pandas, scipy) import ``numpy`` and expect the ``__version__`` attribute as well as
the full NumPy public API.  Importing those libraries raised an ``AttributeError``
because the placeholder module did not provide the required attributes.

This shim re‑exports the genuine NumPy module under the name ``numpy_real`` while
also exposing the ``__version__`` attribute that external packages query.  By
updating the module in‑place we avoid having to touch every consumer of NumPy in
the code base.
"""

import importlib as _importlib
import sys as _sys

# Load the real NumPy implementation
_real_numpy = _importlib.import_module("numpy")

# Export the real NumPy symbols from this shim
globals().update(_real_numpy.__dict__)

# Ensure that ``numpy_real`` presents a ``__version__`` attribute identical to the
# real NumPy package – this satisfies pandas and scipy which read it during import.
__version__ = _real_numpy.__version__

# Also make sure that ``numpy`` resolves to the real implementation even if the
# project directory is earlier on ``sys.path``.  This guards against accidental
# self‑shadowing when ``import numpy`` is executed elsewhere in the repository.
if "numpy" not in _sys.modules:
    _sys.modules["numpy"] = _real_numpy
