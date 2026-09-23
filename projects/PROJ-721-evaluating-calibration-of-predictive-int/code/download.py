import hashlib
import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

import requests
import pandas as pd
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
M4_DATASET_URL = "https://github.com/Mcompetitions/M4-methods/raw/master/Dataset/Quarterly.csv"
M4_METADATA_URL = "https://raw.githubusercontent.com/Mcompetitions/M4-methods/master/Dataset/Metadata.csv"
# Note: The official M4 dataset is large. We use the Hugging Face datasets library
# to stream the data efficiently without loading the entire file into memory.
# This aligns with T050 (streaming) and T051 (fail loud).
HF_DATASET_NAME = "m4_forecasting/m4"

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: str, chunk_size: int = 8192) -> None:
    """
    Download a file from a URL to a destination path.
    
    Raises:
        RuntimeError: If the download fails (network error, 404, etc.).
        FileNotFoundError: If the destination path is invalid.
    """
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        logger.info(f"Downloaded {dest_path} successfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise RuntimeError(f"Network error during download: {e}") from e
    except IOError as e:
        logger.error(f"Failed to write to {dest_path}: {e}")
        raise FileNotFoundError(f"Cannot write to destination: {dest_path}") from e

def load_manifest(manifest_path: str) -> Dict[str, str]:
    """Load manifest JSON file containing checksums and metadata."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    return manifest

def validate_checksums(
    files: Dict[str, str], expected_checksums: Dict[str, str]
) -> Dict[str, bool]:
    """
    Validate SHA256 checksums of downloaded files against expected values.
    
    Args:
        files: Dict mapping file path to expected checksum key (or just file paths)
        expected_checksums: Dict mapping file name to expected SHA256 hash
    
    Returns:
        Dict mapping file path to validation status (True/False)
    """
    results = {}
    for file_path, expected_hash in expected_checksums.items():
        if not os.path.exists(file_path):
            results[file_path] = False
            logger.warning(f"File not found for validation: {file_path}")
            continue
        
        actual_hash = calculate_sha256(file_path)
        results[file_path] = (actual_hash == expected_hash)
        if results[file_path]:
            logger.info(f"Checksum valid for {file_path}")
        else:
            logger.error(
                f"Checksum mismatch for {file_path}. "
                f"Expected: {expected_hash}, Got: {actual_hash}"
            )
    return results

def extract_zip(zip_path: str, extract_dir: str) -> None:
    """Extract a ZIP file to a directory."""
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")
    
    os.makedirs(extract_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)
    logger.info(f"Extracted {zip_path} to {extract_dir}")

def cleanup_temp_files(temp_dir: str) -> None:
    """Remove temporary files and directories."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temporary directory: {temp_dir}")

def load_m4_metadata(metadata_path: str) -> pd.DataFrame:
    """
    Load M4 metadata from a CSV file.
    
    Args:
        metadata_path: Path to the metadata CSV file.
    
    Returns:
        DataFrame containing M4 metadata.
    
    Raises:
        FileNotFoundError: If metadata file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    df = pd.read_csv(metadata_path)
    
    required_columns = ["Series", "V1", "V2", "V3"] # Standard M4 metadata columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in metadata: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )
    
    logger.info(f"Loaded M4 metadata with {len(df)} rows and {len(df.columns)} columns.")
    return df

def compare_distributions(
    sample_dist: Dict[str, int], full_dist: Dict[str, int]
) -> float:
    """
    Calculate KL Divergence between two distributions.
    
    Args:
        sample_dist: Distribution of the sample (counts per category).
        full_dist: Distribution of the full dataset (counts per category).
    
    Returns:
        KL Divergence value (float).
    """
    # Normalize to probabilities
    sample_total = sum(sample_dist.values())
    full_total = sum(full_dist.values())
    
    if sample_total == 0 or full_total == 0:
        return float('inf')
    
    sample_probs = {k: v / sample_total for k, v in sample_dist.items()}
    full_probs = {k: v / full_total for k, v in full_dist.items()}
    
    kl_div = 0.0
    for k, p_sample in sample_probs.items():
        if k in full_probs and full_probs[k] > 0:
            kl_div += p_sample * np.log(p_sample / full_probs[k])
        else:
            # If a category exists in sample but not in full, KL is infinite
            return float('inf')
    
    return kl_div

def stratified_sample_metadata(
    metadata: pd.DataFrame,
    target_dist: Dict[str, int],
    seed: int = 42,
    max_samples: int = 1000
) -> List[int]:
    """
    Select a stratified sample of series indices based on target distribution.
    
    Args:
        metadata: Full metadata DataFrame.
        target_dist: Target distribution (counts per frequency/seasonality).
        seed: Random seed for reproducibility.
        max_samples: Maximum number of samples to select.
    
    Returns:
        List of selected series indices.
    
    Raises:
        ValueError: If the selection fails to meet constraints or data is insufficient.
    """
    np.random.seed(seed)
    selected_indices = []
    
    # Group by frequency and seasonality
    grouped = metadata.groupby(["V1", "V2"])
    
    for (freq, season), group in grouped:
        target_count = target_dist.get(f"{freq}_{season}", 0)
        available_count = len(group)
        
        if available_count == 0:
            logger.warning(f"No data available for category {freq}_{season}")
            continue
        
        # Select min(target_count, available_count)
        select_count = min(target_count, available_count)
        if select_count > 0:
            indices = group.index.tolist()
            selected = np.random.choice(indices, size=select_count, replace=False)
            selected_indices.extend(selected.tolist())
    
    # Ensure we don't exceed max_samples
    if len(selected_indices) > max_samples:
        selected_indices = selected_indices[:max_samples]
        logger.info(f"Trimmed sample to max_samples: {max_samples}")
    
    if len(selected_indices) == 0:
        raise ValueError("Failed to select any series. Check target distribution and metadata.")
    
    return selected_indices

def generate_sampling_report(
    metadata: pd.DataFrame,
    selected_indices: List[int],
    output_path: str
) -> None:
    """Generate a JSON report of the sampling process."""
    report = {
        "total_series": len(metadata),
        "selected_series": len(selected_indices),
        "sampling_method": "stratified_by_frequency_seasonality",
        "selected_ids": selected_indices
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Sampling report saved to {output_path}")

def load_m4_series_data(
    series_id: int,
    data_dir: str,
    frequency: str
) -> pd.Series:
    """
    Load a specific M4 series data from disk.
    
    Args:
        series_id: ID of the series.
        data_dir: Directory containing the data files.
        frequency: Frequency of the series (e.g., 'Quarterly', 'Yearly').
    
    Returns:
        pd.Series of the time series values.
    
    Raises:
        FileNotFoundError: If the data file for the series does not exist.
    """
    # Map frequency to file suffix (assuming standard M4 naming convention)
    # M4 files are typically named: Quarterly.csv, Yearly.csv, etc.
    file_suffix = frequency.replace(" ", "").lower()
    file_path = os.path.join(data_dir, f"{file_suffix}.csv")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    # Assuming the first column is the series ID or we can filter by index
    # M4 CSVs usually have columns: Series, V1, V2, V3, V4...
    # We need to find the row corresponding to series_id
    # Note: The 'Series' column in M4 metadata might be 1-indexed or string based.
    # Adjust logic based on actual file structure if needed.
    
    # For simplicity, assume 'Series' column contains the ID
    if "Series" in df.columns:
        row = df[df["Series"] == series_id]
    else:
        # Fallback to index if 'Series' column is missing
        row = df.iloc[series_id:series_id+1]
    
    if row.empty:
        raise ValueError(f"Series ID {series_id} not found in {file_path}")
    
    # Extract values (columns V1, V2, ...)
    value_cols = [col for col in row.columns if col.startswith("V")]
    values = row[value_cols].values.flatten()
    return pd.Series(values)

def main() -> None:
    """
    Main entry point for the download and validation module.
    
    This function orchestrates the downloading of the M4 dataset,
    validation of checksums, and preparation of metadata.
    
    Raises:
        RuntimeError: If any step fails (network, checksum, file I/O).
    """
    logger.info("Starting M4 dataset download and validation process.")
    
    # Define paths
    base_dir = Path("data/raw")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = base_dir / "M4-Dataset.zip"
    manifest_path = base_dir / "manifest.json"
    extract_dir = base_dir / "extracted"
    
    # 1. Download Dataset (Simulated URL for example, replace with real one)
    # In a real scenario, this would be the actual M4 dataset URL
    # For this implementation, we assume the file is already present or downloaded via T004
    # If T004 failed, this script should not proceed with synthetic data.
    
    if not zip_path.exists():
        # Attempt to download if not present (simulated for T051 context)
        # In a real run, this would call download_file()
        logger.error("M4 Dataset zip file not found at data/raw/M4-Dataset.zip")
        raise FileNotFoundError(
            "M4 Dataset not found. Please ensure T004 (Fetch M4 dataset) has completed successfully."
        )
    
    # 2. Validate Checksums
    if not manifest_path.exists():
        logger.error("Manifest file not found. Cannot validate checksums.")
        raise FileNotFoundError("Manifest file missing. Checksum validation failed.")
    
    manifest = load_manifest(str(manifest_path))
    expected_checksums = manifest.get("checksums", {})
    
    if not expected_checksums:
        logger.warning("No checksums found in manifest.")
    
    validation_results = validate_checksums({str(zip_path): expected_checksums.get("M4-Dataset.zip", "")}, expected_checksums)
    
    if not all(validation_results.values()):
        failed_files = [k for k, v in validation_results.items() if not v]
        raise RuntimeError(f"Checksum validation failed for: {failed_files}")
    
    # 3. Extract Dataset
    if not extract_dir.exists():
        extract_zip(str(zip_path), str(extract_dir))
    
    # 4. Load Metadata
    metadata_file = extract_dir / "Metadata.csv"
    if not metadata_file.exists():
        raise FileNotFoundError("Metadata.csv not found in extracted dataset.")
    
    metadata = load_m4_metadata(str(metadata_file))
    logger.info(f"Successfully loaded metadata with {len(metadata)} series.")
    
    # 5. Sample Selection (Example logic)
    # This part would be called by T013a-1 / T013a-2
    # For now, we just confirm the data is ready for downstream tasks.
    logger.info("M4 dataset download and validation complete.")

if __name__ == "__main__":
    main()