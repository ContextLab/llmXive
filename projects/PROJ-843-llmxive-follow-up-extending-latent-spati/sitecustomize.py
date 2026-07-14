"""
Small site‑customisation module that patches third‑party imports
which are missing in the runtime environment.

Currently it adds ``HfHubHTTPError`` to the ``huggingface_hub`` package
if the attribute is absent.  This prevents an ``ImportError`` in
``code/eval/download_dense_baseline.py`` without altering any other
source file.
"""

import importlib
import sys

try:
    import huggingface_hub as _hf
except Exception:
    # If the package cannot be imported at all, we let the original
    # ImportError propagate – the project truly depends on it.
    raise

if not hasattr(_hf, "HfHubHTTPError"):
    class HfHubHTTPError(Exception):
        """Fallback error type used by older versions of ``huggingface_hub``."""
        pass

    _hf.HfHubHTTPError = HfHubHTTPError
    # Ensure the patched module is the one other imports receive.
    sys.modules["huggingface_hub"] = _hf