import hashlib
import json
import os
import shutil
import zipfile
import logging
import random
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for data paths (relative to project root)
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
STATE_DIR = "state"

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: str) -> None:
    """Download a file from a URL to a destination path."""
    import urllib.request
    logger.info(f"Downloading {url} to {dest_path}")
    urllib.request.urlretrieve(url, dest_path)

def load_manifest(manifest_path: str) -> Dict[str, str]:
    """Load manifest JSON file."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def validate_checksums(downloaded_file: str, manifest: Dict[str, str]) -> bool:
    """Validate SHA256 checksums against manifest."""
    calculated = calculate_sha256(downloaded_file)
    expected = manifest.get(os.path.basename(downloaded_file))
    if not expected:
        logger.error(f"No checksum found for {downloaded_file} in manifest")
        return False
    if calculated != expected:
        logger.error(f"Checksum mismatch for {downloaded_file}: {calculated} != {expected}")
        return False
    logger.info(f"Checksum verified for {downloaded_file}")
    return True

def extract_zip(zip_path: str, extract_to: str) -> None:
    """Extract a ZIP file to a directory."""
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def cleanup_temp_files(temp_dir: str) -> None:
    """Remove temporary extraction directory."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def load_m4_metadata(extracted_dir: str) -> pd.DataFrame:
    """
    Load M4 dataset metadata (frequencies, seasonality, series counts).
    Assumes the standard M4 structure where 'M4-Dataset.zip' contains
    'M4-Dataset/Information.csv' or similar, but primarily relies on
    the manifest or a dedicated metadata file if available.
    
    For this implementation, we assume the extracted directory contains
    'M4-Dataset' folder with 'Information.csv' which has columns:
    'Series', 'Frequency', 'Seasonality', 'Category'.
    """
    info_path = os.path.join(extracted_dir, "M4-Dataset", "Information.csv")
    if not os.path.exists(info_path):
        # Fallback: look in root if structure is flat
        info_path = os.path.join(extracted_dir, "Information.csv")
    
    if not os.path.exists(info_path):
        raise FileNotFoundError(f"Could not find M4 metadata file at {info_path}")

    df = pd.read_csv(info_path)
    # Ensure required columns exist
    required_cols = ['Series', 'Frequency', 'Seasonality']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Metadata missing required columns: {missing}")
    
    return df[['Series', 'Frequency', 'Seasonality']].copy()

def compare_distributions(
    full_counts: Counter, 
    sample_counts: Counter, 
    total_full: int, 
    total_sample: int
) -> float:
    """
    Calculate Chi-squared statistic to compare distributions.
    Returns a 'representativeness' score: 1.0 - (normalized_chi_sq / max_possible).
    A score >= 0.90 indicates the sample is representative.
    
    Note: We normalize the Chi-squared statistic to get a score in [0, 1].
    """
    all_categories = set(full_counts.keys()) | set(sample_counts.keys())
    
    chi_sq = 0.0
    for cat in all_categories:
        expected = (full_counts[cat] / total_full) * total_sample
        observed = sample_counts[cat]
        if expected > 0:
            chi_sq += ((observed - expected) ** 2) / expected
        
    # Normalization: The max chi-sq depends on the distribution, 
    # but a simple heuristic for "representativeness" is to ensure 
    # the deviation is small relative to the sample size.
    # A strict Chi-sq test might reject large samples even for tiny deviations.
    # We use a normalized metric: 1 - min(1, chi_sq / (total_sample * 0.1))
    # This ensures that if chi_sq is very small relative to sample size, score is near 1.
    # Alternatively, we can use the proportion of categories with <= 10% deviation.
    
    # Let's use a simpler, more robust metric for "representativeness" in this context:
    # The fraction of the total distribution captured correctly.
    # We calculate the KL divergence or a similar metric, but Chi-sq is requested.
    # To make Chi-sq a "score >= 0.90", we define:
    # Score = 1 / (1 + chi_sq / total_sample)  -> This approaches 1 as chi_sq -> 0.
    
    score = 1.0 / (1.0 + (chi_sq / total_sample))
    return score

def stratified_sample_metadata(
    metadata_df: pd.DataFrame, 
    target_size: int, 
    seed: int = 42
) -> pd.DataFrame:
    """
    Perform stratified sampling on the metadata dataframe.
    Stratifies by 'Frequency' and 'Seasonality'.
    Uses proportional allocation to match the full dataset's distribution.
    
    Args:
        metadata_df: DataFrame with 'Series', 'Frequency', 'Seasonality'.
        target_size: Number of samples to select.
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame of sampled series indices.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Group by stratification columns
    grouped = metadata_df.groupby(['Frequency', 'Seasonality'])
    
    # Calculate proportional allocation
    total_count = len(metadata_df)
    sample_counts = {}
    
    for (freq, seas), group in grouped:
        group_size = len(group)
        # Proportional allocation
        n_sample = int(round((group_size / total_count) * target_size))
        # Ensure at least 1 if the group exists and we need samples, 
        # but strictly proportional might yield 0 for very small groups.
        # The task says "match the frequency distribution", so 0 is okay if proportion is tiny.
        # However, to ensure we get 'target_size', we might need to adjust.
        # Let's stick to strict proportional first, then adjust if sum != target_size.
        sample_counts[(freq, seas)] = max(0, n_sample)
    
    # Adjust to hit target_size exactly (distribute remainder)
    current_sum = sum(sample_counts.values())
    remainder = target_size - current_sum
    
    # Add remainder to largest groups or randomly
    if remainder != 0:
        groups = list(sample_counts.keys())
        # Sort by group size descending to add to larger groups first
        groups_sorted = sorted(groups, key=lambda k: grouped.get_group(k).size, reverse=True)
        for i in range(abs(remainder)):
            idx = i % len(groups_sorted)
            sample_counts[groups_sorted[idx]] += 1 if remainder > 0 else -1
    
    # Perform sampling
    sampled_indices = []
    for (freq, seas), n in sample_counts.items():
        if n > 0:
            group = grouped.get_group((freq, seas))
            # Sample n rows
            sampled = group.sample(n=n, random_state=seed)
            sampled_indices.extend(sampled.index.tolist())
    
    # Return the sampled rows
    return metadata_df.loc[sampled_indices].reset_index(drop=True)

def generate_sampling_report(
    metadata_df: pd.DataFrame,
    sampled_df: pd.DataFrame,
    sample_indices: List[int],
    metric_threshold: float = 0.90
) -> Dict[str, Any]:
    """
    Generate a JSON report of the sampling process.
    
    Args:
        metadata_df: Full metadata.
        sampled_df: Sampled metadata.
        sample_indices: List of original indices.
        metric_threshold: Minimum representativeness score required.
        
    Returns:
        Dictionary with report data.
    """
    # Calculate full distribution
    full_counts = Counter(metadata_df['Frequency'])
    total_full = len(metadata_df)
    
    # Calculate sample distribution
    sample_counts = Counter(sampled_df['Frequency'])
    total_sample = len(sampled_df)
    
    # Calculate metric
    representativeness = compare_distributions(
        full_counts, sample_counts, total_full, total_sample
    )
    
    report = {
        "full_dataset_size": total_full,
        "sample_size": total_sample,
        "target_sample_size": total_sample, # Should match input target
        "full_distribution": dict(full_counts),
        "sample_distribution": dict(sample_counts),
        "representativeness_metric": float(representativeness),
        "metric_threshold": metric_threshold,
        "passes_threshold": representativeness >= metric_threshold,
        "sample_indices": sample_indices,
        "stratification_columns": ["Frequency", "Seasonality"],
        "seed": 42
    }
    
    if not report["passes_threshold"]:
        logger.error(f"Representativeness metric {representativeness:.4f} < {metric_threshold}. Failing task.")
        raise ValueError(f"Sampling representativeness {representativeness:.4f} is below threshold {metric_threshold}.")
    
    logger.info(f"Sampling report generated. Representativeness: {representativeness:.4f}")
    return report

def main():
    """
    Main entry point for T013a.
    1. Load M4 metadata from data/raw (assumed extracted).
    2. Perform stratified sampling (seed=42).
    3. Calculate representativeness metric.
    4. Save report to data/processed/sampling_report.json.
    """
    # Ensure output directory exists
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    # Load metadata
    # The task assumes T004 has downloaded and extracted the data.
    # We look for the extracted content in data/raw/M4-Dataset or similar.
    # Based on T004 description: "Download ... to data/raw/".
    # We assume the zip is extracted to data/raw/M4-Dataset or we extract it here.
    
    zip_path = os.path.join(RAW_DATA_DIR, "M4-Dataset.zip")
    extract_dir = os.path.join(RAW_DATA_DIR, "M4-Dataset")
    
    if not os.path.exists(extract_dir):
        if os.path.exists(zip_path):
            logger.info("Extracting M4 dataset...")
            extract_zip(zip_path, extract_dir)
        else:
            raise FileNotFoundError(f"M4-Dataset.zip not found at {zip_path}. Run T004 first.")
    
    metadata_df = load_m4_metadata(extract_dir)
    logger.info(f"Loaded {len(metadata_df)} series from metadata.")
    
    # Target sample size: The task doesn't specify a number, but T013b mentions "1000-series".
    # We will sample a representative set. Let's aim for 1000 as per the next task's context.
    target_size = 1000
    if len(metadata_df) < target_size:
        target_size = len(metadata_df)
    
    logger.info(f"Performing stratified sampling for {target_size} series...")
    sampled_df = stratified_sample_metadata(metadata_df, target_size, seed=42)
    sample_indices = sampled_df.index.tolist()
    
    # Generate report
    report = generate_sampling_report(metadata_df, sampled_df, sample_indices)
    
    # Save report
    report_path = os.path.join(PROCESSED_DATA_DIR, "sampling_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sampling report saved to {report_path}")
    return report

if __name__ == "__main__":
    main()
