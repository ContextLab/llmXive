"""
Epigenetic Drift Analysis Pipeline — top-level package marker.

This file makes the ``code/`` directory a Python package. It is kept
intentionally free of eager imports so that importing ``code`` (or any
of its subpackages) never triggers side effects or import-order
failures in the pipeline entry points (e.g. ``python code/main.py``,
which places ``code/`` itself on ``sys.path`` and imports modules such
as ``config`` and ``analysis`` as top-level modules).
"""

__version__ = "0.1.0"
__author__ = "llmXive Research Team"
