"""
Data processing module for Recipe1M analysis.
"""
from .preprocess import (
    build_canonical_map,
    merge_counts,
    compute_marginal_counts,
    normalize_ingredients,
    log_event
)
from .download import download_datasets
from .verify import verify_data_sources

__all__ = [
    'build_canonical_map',
    'merge_counts',
    'compute_marginal_counts',
    'normalize_ingredients',
    'log_event',
    'download_datasets',
    'verify_data_sources'
]
