"""
Wrapper for the HCP download script.

Provides the same ``main`` entry point as ``code.src.data.download_hcp`` so that
external callers can use ``src.data.download_hcp``.
"""

from code.src.data.download_hcp import main

__all__ = ["main"]
