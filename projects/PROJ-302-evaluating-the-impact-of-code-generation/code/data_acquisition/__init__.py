"""
Package initializer for the data_acquisition module.
Exposes the ``main`` entry point for the pipeline.
"""

# Re-export the main function from the implementation module.
from .data_acquisition import main  # noqa: F401
