"""
Ingestion module for the Sensitivity of Regression Coefficients project.

This module handles data fetching, validation, and profiling of datasets
to assess OLS assumption violations.
"""

from .downloader import download_dataset, ingest_and_profile
from .profiler import compute_violation_metrics, classify_severity

__all__ = [
    "download_dataset",
    "ingest_and_profile",
    "compute_violation_metrics",
    "classify_severity",
]