"""
Data ingestion module for downloading and filtering the MP dataset.
"""
import os
import sys
import json
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import requests

from config import load_paths, load_env
from utils.logging import setup_logging, get_logger, PhaseTimer
from utils.sampling import sample_by_chemical_family
from utils.chemical_families import assign_chemical_family


logger = get_logger(__name__)


def get_dataset_download_url() -> str:
    """
    Get the download URL for the MP dataset.

    Returns:
        The download URL.
    """
    # In a real implementation, this would fetch the URL from an API or config
    # For now, we'll use a placeholder that would be replaced by the actual URL
    # This is a simplified version - in production, you'd use the MPDS API
    return "https://example.com/mp-2020.12.1.csv"


def download_file(url: str, output_path: str) -> bool:
    """
    Download a file from a URL.

    Args:
        url: The URL to download from.
        output_path: The path to save the file to.

    Returns:
        True if download was successful, False otherwise.
    """
    try:
        logger.info(f"Downloading {url} to {output_path}")
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {str(e)}")
        return False


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        The SHA-256 checksum as a hexadecimal string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def is_inorganic(composition: str) -> bool:
    """
    Check if a composition is inorganic.

    Args:
        composition: The chemical composition string.

    Returns:
        True if inorganic, False otherwise.
    """
    # Simplified check - in production, use pymatgen or similar
    # Organic compounds typically contain C and H
    if "C" in composition and "H" in composition:
        return False
    return True


def filter_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataset for inorganic compounds.

    Args:
        df: The input DataFrame.

    Returns:
        The filtered DataFrame.
    """
    logger.info(f"Filtering dataset: {len(df)} rows before filtering")
    df = df[df["composition"].apply(is_inorganic)]
    logger.info(f"Filtered dataset: {len(df)} rows after filtering")
    return df


def main() -> None:
    """Main entry point for the ingestion module."""
    setup_logging()

    paths = load_paths()
    raw_dir = Path(paths["raw"])
    processed_dir = Path(paths["processed"])
    evaluation_dir = Path(paths["evaluation"])
    logs_dir = Path(paths["logs"])

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    with PhaseTimer("Ingestion", logger) as timer:
        # Download dataset
        url = get_dataset_download_url()
        output_path = raw_dir / "mp-2020.12.1.csv"

        # Try to download
        if not download_file(url, str(output_path)):
            # Try local fallback
            local_path = raw_dir / "mp-2020.csv"
            if local_path.exists():
                logger.info(f"Using local fallback: {local_path}")
                output_path = local_path
            else:
                raise RuntimeError("CRITICAL: No data available (API failed, local fallback missing). Pipeline cannot proceed.")

        # Calculate checksum
        checksum = calculate_sha256(str(output_path))
        logger.info(f"Dataset checksum: {checksum}")

        # Save checksum
        verification_path = evaluation_dir / "dataset_verification.json"
        with open(verification_path, "w") as f:
            json.dump({"checksum": checksum, "file": str(output_path)}, f, indent=2)

        # Load and filter dataset
        df = pd.read_csv(output_path)
        df = filter_dataset(df)

        # Check row count
        from config import load_paths
        cfg = load_paths()
        # Assuming ROW_THRESHOLD is defined in config
        row_threshold = 100000  # Default value, should come from config
        min_rows = 1000  # Default value, should come from config

        if len(df) < row_threshold:
            logger.info(f"Dataset has {len(df)} rows, which is below threshold {row_threshold}. Saving filtered dataset.")
            filtered_path = raw_dir / "mp-2020.12.1_filtered.csv"
            df.to_csv(filtered_path, index=False)
        else:
            logger.info(f"Dataset has {len(df)} rows, which exceeds threshold {row_threshold}. Performing stratified sampling.")
            random_seed = 42  # Default value, should come from config
            sampled_df = sample_by_chemical_family(df, row_threshold, random_state=random_seed)

            # Validate sampling impact
            if len(sampled_df) < min_rows:
                raise RuntimeError(f"Sampling reduced dataset below minimum statistical power ({min_rows} rows)")

            # Save sampled dataset
            sampled_path = processed_dir / "sampled_raw_data.csv"
            sampled_df.to_csv(sampled_path, index=False)

            # Save sampling manifest
            manifest = {
                "row_count_original": len(df),
                "row_count_sampled": len(sampled_df),
                "random_seed": random_seed,
                "checksum": calculate_sha256(str(sampled_path))
            }
            manifest_path = processed_dir / "sampling_manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)

            # Log sampling stats
            sampling_log = logs_dir / "sampling.log"
            with open(sampling_log, "w") as f:
                json.dump(manifest, f, indent=2)

            # Perform KS test
            from scipy import stats
            ks_stat, p_value = stats.ks_2samp(
                df["formation_energy"].dropna(),
                sampled_df["formation_energy"].dropna()
            )
            ks_result = {
                "ks_statistic": ks_stat,
                "p_value": p_value
            }
            ks_path = evaluation_dir / "sampling_statistics.json"
            with open(ks_path, "w") as f:
                json.dump(ks_result, f, indent=2)

            # Log sampling impact
            impact_log = logs_dir / "sampling_impact.log"
            impact_data = {
                "row_count_original": len(df),
                "row_count_sampled": len(sampled_df),
                "sampling_ratio": len(sampled_df) / len(df),
                "ks_p_value": p_value
            }
            with open(impact_log, "w") as f:
                json.dump(impact_data, f, indent=2)

    logger.info("Ingestion completed successfully")


if __name__ == "__main__":
    main()
