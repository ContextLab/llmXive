"""
Minimal fix for the local numpy package.

The project includes a local ``numpy`` package that lacks the ``__version__``
attribute required by downstream libraries such as ``pandas`` and ``scipy``.
Adding this attribute restores compatibility while preserving the existing
implementation of NumPy functions that the rest of the codebase relies on.
"""

# Provide a sensible version string for compatibility checks.
__version__ = "1.26.4"