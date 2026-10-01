import hashlib
import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, destination: str) -> None:
    """Download a file from a URL."""
    # Implementation depends on specific library (e.g., requests)
    # Placeholder for actual implementation
    pass

def load_manifest(manifest_path: str) -> Dict[str, str]:
    """Load manifest.json containing checksums."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def validate_checksums(file_path: str, expected_checksum: str) -> bool:
    """Validate file checksum against expected value."""
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def extract_zip(zip_path: str, extract_to: str) -> None:
    """Extract a zip file to a directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def cleanup_temp_files(temp_dir: str) -> None:
    """Remove temporary directory and contents."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def load_m4_metadata(metadata_path: str) -> pd.DataFrame:
    """Load M4 metadata from CSV/JSON."""
    if metadata_path.endswith('.csv'):
        return pd.read_csv(metadata_path)
    elif metadata_path.endswith('.json'):
        return pd.DataFrame([json.loads(line) for line in open(metadata_path)])
    else:
        raise ValueError(f"Unsupported metadata format: {metadata_path}")

def compare_distributions(sample_dist: Dict[str, int], full_dist: Dict[str, int]) -> float:
    """Calculate KL divergence between two distributions.

    Args:
        sample_dist: Distribution of the sample (keys: categories, values: counts).
        full_dist: Distribution of the full dataset.

    Returns:
        KL divergence value.
    """
    # Normalize to probabilities
    total_sample = sum(sample_dist.values())
    total_full = sum(full_dist.values())

    if total_sample == 0 or total_full == 0:
        return float('inf')

    p_sample = {k: v / total_sample for k, v in sample_dist.items()}
    p_full = {k: v / total_full for k, v in full_dist.items()}

    # Calculate KL divergence
    kl_div = 0.0
    for k in p_sample.keys():
        if p_sample[k] > 0 and k in p_full and p_full[k] > 0:
            kl_div += p_sample[k] * (p_sample[k] / p_full[k])
    return kl_div

def stratified_sample_metadata(
    metadata: pd.DataFrame,
    target_distribution: Dict[str, int],
    seed: int,
    max_samples: int = 1000,
    min_length: int = 50
) -> List[str]:
    """Select a stratified sample of series to match target distribution.

    Args:
        metadata: DataFrame with columns 'id', 'frequency', 'seasonality', 'length'.
        target_distribution: Target counts per category (e.g., frequency).
        seed: Random seed for reproducibility.
        max_samples: Maximum number of series to select.
        min_length: Minimum length of series to include.

    Returns:
        List of selected series IDs.
    """
    np = __import__('numpy')
    np_rng = np.random.RandomState(seed)

    # Filter out short series
    valid_metadata = metadata[metadata['length'] > min_length].copy()

    if valid_metadata.empty:
        logger.warning("No series longer than min_length found.")
        return []

    # Group by frequency (stratification key)
    groups = valid_metadata.groupby('frequency')

    selected_ids = []

    # Determine selection counts per group to minimize KL divergence
    # Simple heuristic: proportional sampling
    total_valid = len(valid_metadata)
    for freq, group in groups:
        # Calculate proportion in full dataset
        prop = len(group) / total_valid
        # Target count for this group
        target_count = int(prop * max_samples)
        # Clamp to available
        actual_count = min(target_count, len(group))
        if actual_count > 0:
            indices = np_rng.choice(group.index, size=actual_count, replace=False)
            selected_ids.extend(group.loc[indices, 'id'].tolist())

    # Trim to max_samples if necessary
    if len(selected_ids) > max_samples:
        selected_ids = selected_ids[:max_samples]

    return selected_ids

def generate_sampling_report(
    selected_ids: List[str],
    method: str,
    seed: int,
    output_path: str
) -> None:
    """Generate a JSON report documenting the sampling process.

    Args:
        selected_ids: List of selected series IDs.
        method: Description of the sampling method used.
        seed: Random seed used.
        output_path: Path to write the JSON report.
    """
    report = {
        "sample_size": len(selected_ids),
        "sampling_method": method,
        "seed": seed,
        "timestamp": str(pd.Timestamp.now()),
        "selected_series_ids": selected_ids
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Sampling report saved to {output_path}")

def load_m4_series_data(series_id: str, data_dir: str) -> Optional[pd.Series]:
    """Load a specific M4 time series by ID."""
    # Implementation depends on directory structure of extracted M4
    file_path = os.path.join(data_dir, f"{series_id}.csv")
    if os.path.exists(file_path):
        return pd.read_csv(file_path, header=None, squeeze=True)
    return None

def main():
    """Main entry point for download and sampling logic."""
    # Placeholder for CLI argument parsing
    pass

# T053: Explicit sample size logging implementation
def log_sample_metadata(
    selected_ids: List[str],
    method: str,
    seed: int,
    nominal_levels: List[float],
    output_path: str
) -> None:
    """Log explicit sample metadata to a JSON file.

    This function fulfills T053 requirements:
    - Logs exact number of series selected.
    - Logs the sampling method (e.g., "stratified by frequency").
    - Logs the seed used.
    - Includes nominal levels for context.

    Args:
        selected_ids: List of selected series IDs.
        method: Description of the sampling method.
        seed: Random seed used for sampling.
        nominal_levels: List of nominal coverage levels (from config).
        output_path: Path to write the JSON metadata file.
    """
    metadata = {
        "sample_size": len(selected_ids),
        "sampling_method": method,
        "seed": seed,
        "nominal_levels": nominal_levels,
        "timestamp": str(pd.Timestamp.now()),
        "series_ids": selected_ids
    }

    # Ensure directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Sample metadata logged to {output_path}: {len(selected_ids)} series selected using '{method}' (seed={seed}).")

# Re-export main to satisfy existing API surface expectations
# (The existing surface lists 'main' as a public name)
__all__ = [
    "calculate_sha256", "download_file", "load_manifest", "validate_checksums",
    "extract_zip", "cleanup_temp_files", "load_m4_metadata", "compare_distributions",
    "stratified_sample_metadata", "generate_sampling_report", "load_m4_series_data",
    "main", "log_sample_metadata"
]
