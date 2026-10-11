"""
Compatibility wrapper for the ``Species`` Pydantic model.

The original code base expects a module ``code.models.species`` that
exports a ``Species`` class.  To avoid touching many import statements,
we simply re‑export the implementation from ``code.models.schemas``.
"""

from .schemas import Species

__all__ = ["Species"]
