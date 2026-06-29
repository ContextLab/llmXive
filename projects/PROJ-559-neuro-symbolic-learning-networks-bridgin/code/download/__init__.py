"""
Dataset fetching and download utilities.
This module provides interfaces to fetch educational datasets (e.g., ASSISTments)
and prepare them for the neuro-symbolic learning pipeline.
"""
from .fetch_assistments import fetch_assistments_dataset
from .fetch_assistments import download_raw_csv

__all__ = [
    "fetch_assistments_dataset",
    "download_raw_csv",
]
