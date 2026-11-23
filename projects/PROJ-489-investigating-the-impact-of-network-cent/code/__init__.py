"""
Package initialization for the project.

This file ensures that required attributes are available in imported
third‑party modules before other project modules are imported.
"""

# Patch scipy.signal to provide a ``coherency`` alias for compatibility.
# The original implementation used ``scipy.signal.coherency`` which does not
# exist in recent SciPy versions. The standard function is ``coherence``.
# By assigning the alias here, any subsequent ``from scipy.signal import
# coherency`` statements succeed without modifying the original source
# files.
try:
    import scipy.signal as _signal
    if not hasattr(_signal, "coherency"):
        _signal.coherency = _signal.coherence  # type: ignore[attr-defined]
except Exception:
    # If SciPy is not available for any reason, the import will fail later
    # where the actual usage occurs. Silently ignore here to keep package
    # importable.
    pass
