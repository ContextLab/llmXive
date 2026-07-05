"""
Data module for alloy diffusion research.
Contains acquisition, ingestion, curation, and checksum utilities.
"""
from .checksum import (
    compute_sha256,
    generate_checksums,
    save_checksums,
    load_checksums,
    verify_checksums,
    main as checksum_main
)

__all__ = [
    "compute_sha256",
    "generate_checksums",
    "save_checksums",
    "load_checksums",
    "verify_checksums",
    "checksum_main"
]
