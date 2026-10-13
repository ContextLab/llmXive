"""
Compatibility shim for ``code.datasets.download_datasets``.

The core download utilities are provided by ``src.datasets.download_datasets``.
This module simply forwards the CLI entry point so that the path specified
in the task description (``code/datasets/download_datasets.py``) is
executable.
"""

from src.datasets.download_datasets import main  # noqa: F401
