"""Compatibility wrapper for the reference engine.

The original implementation resides in ``code.generators.reference_engine``.
Tests import ``generators.reference_engine``; this wrapper simply re‑exports
the class so that both import styles resolve to the same implementation.
"""

from code.generators.reference_engine import ReferenceEngine  # noqa: F401

__all__ = ["ReferenceEngine"]