"""
Ingestion module for dataset download and OLS assumption profiling.

This module exposes the main pipeline function `ingest_and_profile` which:
1. Downloads a dataset from a verified source (HuggingFace/UCI).
2. Profiles the dataset for OLS assumption violations (Breusch-Pagan, Cook's Distance, Condition Number).
3. Saves the resulting `DatasetProfile` as a JSON file in `artifacts/profiles/`.
"""

from .downloader import download_dataset
from .profiler import profile_dataset, ingest_and_profile
from ..models.data_models import DatasetProfile

__all__ = [
    "download_dataset",
    "profile_dataset",
    "ingest_and_profile",
    "DatasetProfile",
]