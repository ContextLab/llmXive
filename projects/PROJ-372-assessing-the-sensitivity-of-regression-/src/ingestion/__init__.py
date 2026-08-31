"""
Ingestion module for the llmXive automated science pipeline.

This module handles the fetching, validation, and initial profiling of raw datasets.
It provides the `ingest_and_profile` pipeline which orchestrates downloading data
from verified sources and computing OLS assumption violation metrics.
"""
from .downloader import download_dataset, verify_checksum
from .profiler import DatasetProfile, compute_profile, ingest_and_profile

__all__ = [
    "download_dataset",
    "verify_checksum",
    "DatasetProfile",
    "compute_profile",
    "ingest_and_profile",
]