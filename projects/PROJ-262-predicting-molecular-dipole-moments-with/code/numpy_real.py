"""
Real numpy shim module.

The project contains a top-level package named ``numpy`` which attempts to
lazily import the real NumPy installation as ``numpy_real``.  The original
shim expects a module called ``numpy_real`` to exist, but it was missing,
causing ``ModuleNotFoundError`` for every ``import numpy`` in the code base.

This file provides the missing ``numpy_real`` module.  It simply re‑exports
the real NumPy package so that the existing shim can load it without any
further changes.
"""

# Import the actual NumPy library and expose it under the name expected by
# the shim (``numpy_real``).  All attributes of the real NumPy module are
# re‑exported, making this module a transparent proxy.
import numpy as _real_numpy

# Populate the module namespace with everything from the real NumPy.
globals().update(_real_numpy.__dict__)

# Ensure ``__all__`` mirrors that of the real NumPy.
__all__ = getattr(_real_numpy, "__all__", [])

# Provide a helpful representation.
def __repr__():
    return f"<numpy_real proxy for {_real_numpy.__name__}>"