"""
Compatibility shim for legacy imports.

The original project places utility modules inside the ``code.utils`` package.
Many existing scripts import them as top‑level ``utils`` (e.g. ``from utils.config import …``).
This shim re‑exports the relevant symbols so those imports resolve without
modifying every script.
"""
# Re‑export commonly used symbols from the actual implementation package.
from .config import *
from .logging_config import *
from .logger import *

__all__ = []
__all__ += config.__all__ if 'config' in globals() else []
__all__ += logging_config.__all__ if 'logging_config' in globals() else []
__all__ += logger.__all__ if 'logger' in globals() else []
