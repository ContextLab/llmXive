"""
Compatibility wrapper for the ``Metabolite`` Pydantic model.

The rest of the code imports ``Metabolite`` from
``code.models.metabolite``; we forward the definition from the central
``schemas`` module.
"""

from .schemas import Metabolite

__all__ = ["Metabolite"]
