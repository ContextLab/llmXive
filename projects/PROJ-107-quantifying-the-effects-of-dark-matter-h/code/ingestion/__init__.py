"""
Ingestion module for loading external datasets.
"""
from .tng_loader import fetch_tng_snapshot_000_halos

__all__ = ["fetch_tng_snapshot_000_halos"]
