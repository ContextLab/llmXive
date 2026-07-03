"""Data module for llmXive research pipeline."""
from .fetch import fetch_dataset
from .preprocess import (
    preprocess_dataset,
    check_data_completeness,
    validate_dataset,
    compute_basic_stats
)

__all__ = [
    "fetch_dataset",
    "preprocess_dataset",
    "check_data_completeness",
    "validate_dataset",
    "compute_basic_stats"
]
