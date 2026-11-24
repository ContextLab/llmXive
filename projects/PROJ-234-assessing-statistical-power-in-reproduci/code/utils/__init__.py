"""
Utility package for the project.

Exposes the public helpers:
- api_client
- oa_checker
- parsers
- DataFetchError
"""
from .api_client import DataFetchError, fetch_top_classification_datasets
from .oa_checker import is_open_access
from .parsers import extract_sample_size, extract_effect_size

__all__ = [
    "DataFetchError",
    "fetch_top_classification_datasets",
    "is_open_access",
    "extract_sample_size",
    "extract_effect_size",
]
