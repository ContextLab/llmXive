"""
Ingestion module for data loading and profiling.
"""
from .downloader import ingest_and_profile
from .profiler import compute_profile_metrics

__all__ = ["ingest_and_profile", "compute_profile_metrics"]
