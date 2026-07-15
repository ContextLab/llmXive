"""
llmXive Automated Science Pipeline - Code Package
"""
__version__ = "0.1.0"

from utils.loaders import load_cot_traces, load_oracle_source_code, load_dataset_from_url
from utils.checksums import (
    compute_file_sha256,
    compute_string_sha256,
    verify_file_checksum,
    generate_checksum_manifest,
    verify_checksum_manifest,
    check_code_drift,
)
from main import main
