"""
Compatibility wrapper for the ``BGCFeature`` Pydantic model.

The pipeline imports ``BGCFeature`` from ``code.models.bgc``; this file
re‑exports the canonical definition from ``code.models.schemas``.
"""

from .schemas import BGCFeature

__all__ = ["BGCFeature"]
