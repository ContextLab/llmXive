# Data package
"""
Data loading and preprocessing modules for the RULER dataset.
Handles dataset fetching, integrity verification, chunking, and streaming.
"""

from .loader import (
    calculate_sha256,
    verify_ruler_data_integrity,
    download_and_verify_ruler,
)
from .preprocess import (
    PreprocessConfig,
    get_available_memory_gb,
    get_used_memory_gb,
    check_memory_pressure,
    reduce_context_window,
    reduce_batch_size,
    stream_dataset_chunks,
    preprocess_and_save,
)
from .ruler_loader import (
    ensure_directory,
    compute_sha256,
    load_ruler_dataset,
    save_dataset_to_disk,
    record_checksums,
)

__all__ = [
    "calculate_sha256",
    "verify_ruler_data_integrity",
    "download_and_verify_ruler",
    "PreprocessConfig",
    "get_available_memory_gb",
    "get_used_memory_gb",
    "check_memory_pressure",
    "reduce_context_window",
    "reduce_batch_size",
    "stream_dataset_chunks",
    "preprocess_and_save",
    "ensure_directory",
    "compute_sha256",
    "load_ruler_dataset",
    "save_dataset_to_disk",
    "record_checksums",
]
