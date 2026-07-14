"""
Data Acquisition Module.

This module handles downloading and validating external datasets and resources.
"""

from .download_agency_scale import compute_sha256, download_file, main as scale_main
from .download_benchmark import (
    load_sources_config,
    compute_sha256 as benchmark_sha256,
    download_file as benchmark_download,
    update_metadata,
    main as benchmark_main,
)
from .download_datasets import main as datasets_main
from .validate_metadata import load_metadata, verify_checksums, main as validate_main

__all__ = [
    "compute_sha256",
    "download_file",
    "load_sources_config",
    "update_metadata",
    "load_metadata",
    "verify_checksums",
    "scale_main",
    "benchmark_sha256",
    "benchmark_download",
    "benchmark_main",
    "datasets_main",
    "validate_main",
]
