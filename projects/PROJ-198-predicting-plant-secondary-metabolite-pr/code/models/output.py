"""
Compatibility wrapper for the ``ModelOutput`` Pydantic model.

Exported as ``ModelOutput`` to keep existing import paths working.
"""

from .schemas import ModelOutput

__all__ = ["ModelOutput"]