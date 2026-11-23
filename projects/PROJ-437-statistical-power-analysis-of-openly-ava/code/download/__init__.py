"""
Download package initializer.
Exposes the primary public functions for the download stage.
"""

from .openneuro_fetcher import download_datasets, main as fetch_main  # noqa: F401
from .data_validator import validate_bids_structure, write_manifest  # noqa: F401
from .corruption_handler import verify_file_integrity, compute_sha256  # noqa: F401
from .streaming_chunker import chunked_reader  # noqa: F401
from .data_integrity_hash import write_integrity_hashes  # noqa: F401
from .sampling_strategy import sample_subjects  # noqa: F401