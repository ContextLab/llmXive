"""
Data module initialization.
Exposes interfaces for data download, processing, and schema.
"""
from src.data.download import (
    calculate_sha256,
    verify_checksum,
    fetch_chembl_smiles,
    fetch_zinc15_smiles,
    fetch_ncbi_resistance_frequencies,
    log_data_version,
    download_all_data
)
from src.data.process import (
    canonicalize_smiles,
    calculate_descriptors,
    process_compounds,
    run_process_pipeline
)
from src.data.schema import DataVersion, DataVersionFile
from src.data.metrics import (
    calculate_merge_metrics,
    save_merge_metrics,
    generate_merge_metrics_report
)
from src.data.utils import (
    FetchError,
    fetch_with_backoff,
    fetch_with_backoff_bytes
)

__all__ = [
    'calculate_sha256',
    'verify_checksum',
    'fetch_chembl_smiles',
    'fetch_zinc15_smiles',
    'fetch_ncbi_resistance_frequencies',
    'log_data_version',
    'download_all_data',
    'canonicalize_smiles',
    'calculate_descriptors',
    'process_compounds',
    'run_process_pipeline',
    'DataVersion',
    'DataVersionFile',
    'calculate_merge_metrics',
    'save_merge_metrics',
    'generate_merge_metrics_report',
    'FetchError',
    'fetch_with_backoff',
    'fetch_with_backoff_bytes'
]
