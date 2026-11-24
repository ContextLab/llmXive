"""Utility package for the project."""
# Export public symbols for convenient imports.
from .data_fetcher import (
    DataFetchError,
    load_ms_marco,
    load_spider,
    load_dbpedia,
)

__all__ = [
    "DataFetchError",
    "load_ms_marco",
    "load_spider",
    "load_dbpedia",
]