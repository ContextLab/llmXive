"""
Compatibility wrapper for the canonical artifact writer.

The original implementation lives in ``code/utils/artifacts.py``.  This
module simply imports the public ``write_artifact`` function from that
location and re‑exports it under the top‑level ``utils`` package, allowing
existing code (e.g. ``code/main.py``) that does ``from utils.artifacts
import write_artifact`` to succeed without any further changes.
"""
from importlib import import_module

# Import the real implementation from the code subpackage.
_impl = import_module("code.utils.artifacts")

# Re‑export the public API.
write_artifact = _impl.write_artifact
