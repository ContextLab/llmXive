import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

# Import config for seed management
from config import SeedManager, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_directories(path: str) -> Path:
    """Ensure the directory for the given path exists."""
    dir_path = Path(path).parent
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def validate_schema(df: pd.DataFrame, meta: Dict[str, Any], schema_path: Optional[str] = None) -> bool:
    """
    Validate the generated data against the dataset schema.
    Checks for required columns and data types.
    """
    required_cols = ['id', 'value', 'missingness_mechanism']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Schema validation failed: missing column '{col}'")
            return False

    # Check meta fields
    meta_required = ['true_mean', 'true_variance', 'missingness_mechanism']
    for field in meta_required:
        if field not in meta:
            logger.error(f"Schema validation failed: missing meta field '{field}'")
            return False

    logger.info("Schema validation passed.")
    return True

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_synthetic_data(
    n: int,
    true_mean: float,
    true_variance: float,
    missing_rate: float,
    mechanism: str,
    seed: int
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generates synthetic data with known super-population parameters.
    The generator creates a normal distribution with the specified mean and variance,
    then injects missingness according to the specified mechanism.
    """
    if mechanism not in ['MCAR', 'MAR']:
        raise ValueError(f"Unsupported mechanism: {mechanism}. Use 'MCAR' or 'MAR'.")

    rng = np.random.default_rng(seed)

    # Generate base data: Normal distribution
    # Variance = std^2, so std = sqrt(variance)
    std_dev = np.sqrt(true_variance)
    values = rng.normal(loc=true_mean, scale=std_dev, size=n)

    # Create missingness mask
    missing_mask = np.zeros(n, dtype=bool)
    
    if mechanism == 'MCAR':
        # Missing Completely At Random: probability independent of value
        missing_mask = rng.random(n) < missing_rate
    elif mechanism == 'MAR':
        # Missing At Random: probability depends on value (e.g., higher values more likely to be missing)
        # Normalize values to [0, 1] for probability scaling
        # Avoid division by zero if variance is 0 (though unlikely in this context)
        if std_dev > 0:
            normalized = (values - values.min()) / (values.max() - values.min() + 1e-8)
            # Create a probability that increases with value
            prob = missing_rate * (0.5 + 0.5 * normalized)
        else:
            prob = np.full(n, missing_rate)
        missing_mask = rng.random(n) < prob

    # Apply mask to create NaNs
    data_values = values.copy()
    data_values[missing_mask] = np.nan

    # Create DataFrame
    df = pd.DataFrame({
        'id': range(1, n + 1),
        'value': data_values,
        'missingness_mechanism': mechanism
    })

    # Prepare metadata
    meta = {
        'true_mean': true_mean,
        'true_variance': true_variance,
        'missingness_mechanism': mechanism,
        'missing_rate': missing_rate,
        'n_rows': n,
        'seed': seed
    }

    return df, meta

def main():
    """
    CLI entry point for generating synthetic data.
    Parses arguments, generates data, validates, and saves to disk.
    """
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for imputation evaluation.")
    parser.add_argument('--n-rows', type=int, default=10000, help='Number of rows to generate.')
    parser.add_argument('--mechanism', type=str, default='MAR', choices=['MCAR', 'MAR'], help='Missingness mechanism.')
    parser.add_argument('--true-mean', type=float, default=50.0, help='True population mean.')
    parser.add_argument('--true-variance', type=float, default=25.0, help='True population variance.')
    parser.add_argument('--missing-rate', type=float, default=0.2, help='Rate of missingness.')
    parser.add_argument('--seed', type=int, default=42, help='Base seed for reproducibility.')
    parser.add_argument('--output-csv', type=str, default='data/processed/synthetic_mar_v1.csv', help='Output CSV path.')
    parser.add_argument('--output-meta', type=str, default='data/processed/synthetic_mar_v1_meta.json', help='Output metadata JSON path.')
    
    args = parser.parse_args()

    logger.info(f"Starting synthetic data generation: n={args.n_rows}, mechanism={args.mechanism}")

    try:
        # Generate data
        df, meta = generate_synthetic_data(
            n=args.n_rows,
            true_mean=args.true_mean,
            true_variance=args.true_variance,
            missing_rate=args.missing_rate,
            mechanism=args.mechanism,
            seed=args.seed
        )

        # Ensure directories exist
        ensure_directories(args.output_csv)
        ensure_directories(args.output_meta)

        # Validate schema
        if not validate_schema(df, meta):
            logger.error("Schema validation failed. Aborting save.")
            sys.exit(1)

        # Save CSV
        df.to_csv(args.output_csv, index=False)
        logger.info(f"Saved synthetic data to {args.output_csv}")

        # Save metadata JSON
        with open(args.output_meta, 'w') as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Saved metadata to {args.output_meta}")

        # Compute and log checksums
        csv_hash = compute_sha256(Path(args.output_csv))
        meta_hash = compute_sha256(Path(args.output_meta))
        logger.info(f"CSV SHA-256: {csv_hash}")
        logger.info(f"Meta SHA-256: {meta_hash}")

        # Update manifest if update_state is available (optional dependency check)
        try:
            from update_state import update_manifest
            update_manifest(
                artifact_path=args.output_csv,
                hash_value=csv_hash,
                status="success"
            )
            update_manifest(
                artifact_path=args.output_meta,
                hash_value=meta_hash,
                status="success"
            )
        except ImportError:
            logger.warning("update_state module not found. Skipping manifest update.")

        logger.info("Synthetic data generation completed successfully.")

    except Exception as e:
        logger.error(f"Error during generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
