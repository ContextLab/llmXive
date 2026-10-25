"""
Package initializer for the data acquisition module.

Exposes the ``main`` function as the public entry point so that
``import code.data_acquisition`` provides direct access to the
pipeline's execution routine without causing circular imports.
"""

# Re-export the ``main`` function from the sibling module.
# The leading dot ensures a relative import within the same package.
from .data_acquisition import main  # noqa: F401
