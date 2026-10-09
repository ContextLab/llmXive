"""
Top‑level wrapper to expose the data‑loader API as ``data_loader``.
This allows tests that import ``from data_loader import EEGDataLoader``
to work without having to know the internal package layout.
"""
from code.data_loader import DataChunk, EEGDataLoader, main

__all__ = ["DataChunk", "EEGDataLoader", "main"]
