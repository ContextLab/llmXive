"""
``code.utils`` package initializer.

The original package attempted to import ``load_config`` and ``save_config``
from ``code.utils.config`` but those symbols were missing, causing import
failures across the project.  The functions have now been added to
``code.utils.config`` (see that file) and are re‑exported here for backward
compatibility.
"""

from .config import load_config, save_config  # noqa: F401

# Export other utility symbols that may be added later.
__all__ = ["load_config", "save_config"]
