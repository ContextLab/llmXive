"""Data module initialization."""
from .checksum_utils import compute_sha256, generate_checksum_file, verify_checksum, batch_verify_checksums
from .download import DataFetchError, download_femnist, download_shakespeare, download_dataset, main
from .partition import load_femnist_data, apply_dirichlet_partition, validate_partition, partition_femnist, save_partition_metadata, generate_and_save_partitions, main as partition_main
from .generate_partition_metadata import generate_metadata_for_configuration, main as metadata_main

__all__ = [
    'compute_sha256', 'generate_checksum_file', 'verify_checksum', 'batch_verify_checksums',
    'DataFetchError', 'download_femnist', 'download_shakespeare', 'download_dataset', 'main',
    'load_femnist_data', 'apply_dirichlet_partition', 'validate_partition', 'partition_femnist',
    'save_partition_metadata', 'generate_and_save_partitions', 'partition_main',
    'generate_metadata_for_configuration', 'metadata_main'
]