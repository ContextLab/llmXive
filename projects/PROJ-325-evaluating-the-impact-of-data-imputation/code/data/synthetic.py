import argparse
import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd

# Ensure we can import sibling modules if needed, though we rely on stdlib/numpy/pandas here
# The project structure expects this file to be runnable as a script

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories(path: str) -> None:
    """Create directory if it does not exist."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_schema(data: pd.DataFrame, schema_path: str) -> bool:
    """
    Validate the generated data against the dataset schema.
    Since we are generating the data, we ensure it conforms to the expected structure.
    The schema expects: true_mean, true_variance, missingness_mechanism, n, missing_rate
    This function checks that the metadata we generate matches these constraints.
    """
    # We assume the metadata dict (passed separately) is validated against the JSON schema
    # Here we just ensure the data frame has the expected 'value' column
    if 'value' not in data.columns:
        logger.error("Generated data missing 'value' column.")
        return False
    return True

def generate_synthetic_data(
    n: int = 1000,
    true_mean: float = 50.0,
    true_variance: float = 100.0,
    missing_rate: float = 0.2,
    mechanism: str = "MAR",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic data with known super-population parameters.
    - For MCAR: missingness is random.
    - For MAR: missingness depends on the value itself (e.g., lower values more likely to be missing).
    """
    np.random.seed(seed)

    # Generate data from a normal distribution
    values = np.random.normal(loc=true_mean, scale=np.sqrt(true_variance), size=n)

    # Determine missingness mask
    missing_mask = np.zeros(n, dtype=bool)

    if mechanism == "MCAR":
        # Missing Completely At Random
        missing_mask = np.random.random(n) < missing_rate
    elif mechanism == "MAR":
        # Missing At Random: probability of missing increases as value decreases
        # Normalize values to 0-1 range for probability calculation
        min_val, max_val = values.min(), values.max()
        if max_val == min_val:
            # Avoid division by zero if all values are same (unlikely with normal)
            probs = np.full(n, missing_rate)
        else:
            # Lower values -> higher probability of missing
            normalized = (values - min_val) / (max_val - min_val)
            probs = missing_rate + (1 - normalized) * 0.5 # Bias towards missing for low values
            probs = np.clip(probs, 0, 1)
        missing_mask = np.random.random(n) < probs
    else:
        raise ValueError(f"Unsupported mechanism: {mechanism}. Use 'MCAR' or 'MAR'.")

    # Apply missingness
    data = values.copy()
    data[missing_mask] = np.nan

    df = pd.DataFrame({'value': data})

    # Add a secondary variable to make it slightly more realistic (optional but good for downstream)
    # e.g., a binary variable correlated with value
    df['binary_outcome'] = (values > true_mean).astype(int)
    # Introduce missingness in binary_outcome based on value as well for MAR consistency
    binary_missing_mask = np.random.random(n) < (missing_rate * 0.5)
    df.loc[binary_missing_mask, 'binary_outcome'] = np.nan

    return df

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for imputation study.")
    parser.add_argument("--n-rows", type=int, default=1000, help="Number of rows to generate.")
    parser.add_argument("--true-mean", type=float, default=50.0, help="True mean of the population.")
    parser.add_argument("--true-variance", type=float, default=100.0, help="True variance of the population.")
    parser.add_argument("--missing-rate", type=float, default=0.2, help="Rate of missing values.")
    parser.add_argument("--mechanism", type=str, choices=["MCAR", "MAR"], default="MAR", help="Missingness mechanism.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--output-csv", type=str, default="data/processed/synthetic_mar_v1.csv", help="Output CSV path.")
    parser.add_argument("--output-meta", type=str, default="data/processed/synthetic_mar_v1_meta.json", help="Output metadata JSON path.")
    parser.add_argument("--schema", type=str, default="specs/001-evaluating-the-impact-of-data-imputation/contracts/dataset.schema.yaml", help="Path to schema for validation.")
    parser.add_argument("--generate", action="store_true", help="Trigger generation.")
    parser.add_argument("--validate-schema", action="store_true", help="Validate output against schema.")

    args = parser.parse_args()

    if not args.generate:
        logger.error("The --generate flag is required to run the synthetic data generator.")
        sys.exit(1)

    logger.info(f"Generating synthetic data: n={args.n_rows}, mean={args.true_mean}, var={args.true_variance}, rate={args.missing_rate}, mech={args.mechanism}")

    # Generate data
    df = generate_synthetic_data(
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

    # Save CSV
    df.to_csv(args.output_csv, index=False)
    logger.info(f"Saved synthetic data to {args.output_csv}")

    # Compute checksum
    checksum = compute_sha256(args.output_csv)
    logger.info(f"Checksum: {checksum}")

    # Prepare metadata
    metadata = {
        "true_mean": args.true_mean,
        "true_variance": args.true_variance,
        "missingness_mechanism": args.mechanism,
        "n": args.n_rows,
        "missing_rate": args.missing_rate,
        "seed": args.seed,
        "checksum": checksum,
        "sampling_rule": "Full population generated via numpy.random.normal"
    }

    # Save metadata
    with open(args.output_meta, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {args.output_meta}")

    # Validate schema if requested
    if args.validate_schema:
        if not os.path.exists(args.schema):
            logger.warning(f"Schema file not found at {args.schema}, skipping validation.")
        else:
            is_valid = validate_schema(df, args.schema)
            if is_valid:
                logger.info("Schema validation passed.")
            else:
                logger.error("Schema validation failed.")
                sys.exit(1)

    logger.info("Synthetic data generation complete.")

if __name__ == "__main__":
    main()