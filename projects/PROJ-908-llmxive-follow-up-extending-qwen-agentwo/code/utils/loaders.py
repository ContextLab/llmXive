"""
Data loading utilities with strict "Fail Loudly" policy.

This module implements Constitution Principle III: Data Hygiene.
All loaders must attempt to fetch REAL data from verified sources.
If a fetch fails, they MUST raise an exception.
NO synthetic fallbacks, NO mock data generation.
"""
import json
import os
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Try to import datasets, but fail gracefully if not installed (though it should be)
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' library is required for T017. Install via pip install datasets.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when a real data fetch fails and no fallback is allowed."""
    pass

def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_cot_traces() -> List[Dict[str, Any]]:
    """
    Fetch real CoT traces from the HuggingFace dataset `qwen-agentworld/cot_traces`.
    
    This function implements T017 requirements:
    - Attempts to fetch from HF.
    - If fetch fails (network, missing dataset), raises DataFetchError.
    - Does NOT generate synthetic data.
    
    Returns:
        List of dictionaries representing the traces.
    """
    dataset_name = "qwen-agentworld/cot_traces"
    logger.info(f"Attempting to fetch dataset: {dataset_name}")

    try:
        # Attempt to load the dataset
        # Using streaming=False to ensure we get the full list for validation,
        # but if the dataset is huge, we might need to adjust.
        # For T017, we assume a manageable size for the initial fetch.
        ds = load_dataset(dataset_name, split="train")
        
        if ds is None or len(ds) == 0:
            raise DataFetchError(f"Dataset {dataset_name} loaded but contains no records.")

        # Convert to list of dicts
        traces = ds.to_list()
        logger.info(f"Successfully loaded {len(traces)} traces from {dataset_name}.")
        
        # Basic validation of structure
        if traces:
            required_keys = {"task_id", "interaction_type", "steps"}
            first = traces[0]
            missing = required_keys - set(first.keys())
            if missing:
                logger.warning(f"Dataset missing expected keys: {missing}. Proceeding anyway.")

        return traces

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to fetch real CoT traces from {dataset_name}: {error_msg}")
        
        # Explicitly check for common failure modes to provide a clear error
        if "404" in error_msg or "not found" in error_msg.lower():
            raise DataFetchError(f"Dataset '{dataset_name}' not found on HuggingFace Hub. "
                                 "Cannot proceed without real data.") from e
        
        raise DataFetchError(f"Failed to fetch dataset '{dataset_name}'. "
                             "Network error or source unavailable. "
                             "Falling back to synthetic data is FORBIDDEN.") from e

def load_oracle_source_code() -> List[Dict[str, Any]]:
    """
    Load the source code for the Oracle from the benchmark.
    This is a placeholder for future implementation if source code needs to be fetched.
    """
    raise NotImplementedError("Oracle source code loading not yet implemented.")

def load_dataset_from_url(url: str) -> List[Dict[str, Any]]:
    """
    Load a dataset from a raw JSON URL.
    """
    raise NotImplementedError("Direct URL loading not yet implemented for this task.")

def verify_agentworld_bench_integrity(file_path: Path, expected_hash: str) -> bool:
    """
    Verify the integrity of a downloaded file against an expected hash.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} not found for verification.")
    
    actual_hash = compute_file_sha256(file_path)
    if actual_hash != expected_hash:
        raise ValueError(f"Checksum mismatch for {file_path}. Expected {expected_hash}, got {actual_hash}")
    
    logger.info(f"Integrity verified for {file_path}")
    return True

def fetch_agentworld_bench_with_verification(output_path: Path, expected_hash: str) -> Path:
    """
    Fetch the benchmark and verify its integrity.
    """
    # This is a placeholder for the actual fetch logic which would be in T016a
    raise NotImplementedError("Benchmark fetch logic is in T016a.")

def load_dataset_from_hf_with_verification(dataset_name: str, expected_hash: str) -> List[Dict[str, Any]]:
    """
    Fetch a dataset from HF and verify its integrity.
    """
    # This is a placeholder for T016a logic
    raise NotImplementedError("HF verification logic is in T016a.")
