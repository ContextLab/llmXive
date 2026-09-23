import argparse
import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure required output directories exist."""
    dirs = [
        Path("data/processed"),
        Path("data/raw/cache"),
        Path("state")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured directories exist.")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_schema(data: pd.DataFrame, meta: Dict[str, Any], mechanism: str) -> bool:
    """
    Validate the generated data and metadata against the project schema.
    Checks:
    1. CSV has required columns: 'value', 'missing'
    2. Meta has required keys: true_mean, true_variance, missingness_mechanism
    3. Mechanism in meta matches the requested mechanism
    """
    required_csv_cols = ['value', 'missing']
    if not all(col in data.columns for col in required_csv_cols):
        logger.error(f"CSV missing columns: {required_csv_cols}")
        return False

    required_meta_keys = ['true_mean', 'true_variance', 'missingness_mechanism']
    if not all(key in meta for key in required_meta_keys):
        logger.error(f"Meta missing keys: {required_meta_keys}")
        return False

    if meta['missingness_mechanism'] != mechanism:
        logger.error(f"Meta mechanism '{meta['missingness_mechanism']}' != requested '{mechanism}'")
        return False

    logger.info("Schema validation passed.")
    return True

def generate_synthetic_data(
    n: int = 1000,
    true_mean: float = 50.0,
    true_variance: float = 100.0,
    missing_rate: float = 0.2,
    mechanism: str = "MCAR",
    seed: int = 42
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate synthetic data with known super-population parameters.

    Args:
        n: Number of samples.
        true_mean: Population mean.
        true_variance: Population variance.
        missing_rate: Proportion of missing values.
        mechanism: 'MCAR' or 'MAR'.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (DataFrame with 'value' and 'missing' columns, metadata dict).
    """
    np.random.seed(seed)
    logger.info(f"Generating synthetic data: n={n}, mean={true_mean}, var={true_variance}, rate={missing_rate}, mechanism={mechanism}")

    # Generate base data from normal distribution
    # We generate N(0, 1) then scale and shift
    base_data = np.random.normal(loc=0.0, scale=1.0, size=n)
    # Scale to target variance: Var(aX + b) = a^2 Var(X). We want a^2 * 1 = true_variance => a = sqrt(true_variance)
    # Shift to target mean: E[aX + b] = b = true_mean
    data_values = base_data * np.sqrt(true_variance) + true_mean

    # Create mask
    missing_mask = np.zeros(n, dtype=bool)

    if mechanism == "MCAR":
        # Missing Completely At Random: independent of data values
        missing_mask = np.random.random(n) < missing_rate
    elif mechanism == "MAR":
        # Missing At Random: probability depends on observed covariates.
        # Since we only have one variable 'value', we use the value itself to determine probability.
        # Logistic function: p = 1 / (1 + exp(-(x - threshold)/scale))
        # We center the threshold at the mean so roughly half the "risk" is above/below.
        # We scale so that the resulting average probability is approx missing_rate.
        threshold = true_mean
        scale = np.sqrt(true_variance) / 2.0  # Adjust spread
        # Calculate raw probabilities
        logits = (data_values - threshold) / scale
        probs = 1 / (1 + np.exp(-logits))
        
        # Normalize probs to match target missing_rate exactly
        current_mean_prob = np.mean(probs)
        if current_mean_prob > 0:
            probs = probs * (missing_rate / current_mean_prob)
        probs = np.clip(probs, 0, 1)
        
        missing_mask = np.random.random(n) < probs
    else:
        raise ValueError(f"Unsupported mechanism: {mechanism}. Use 'MCAR' or 'MAR'.")

    df = pd.DataFrame({
        'value': data_values,
        'missing': missing_mask
    })

    # Apply mask to values (set to NaN where missing is True)
    df.loc[df['missing'], 'value'] = np.nan

    metadata = {
        'true_mean': true_mean,
        'true_variance': true_variance,
        'missingness_mechanism': mechanism,
        'n': n,
        'missing_rate': missing_rate,
        'seed': seed
    }

    return df, metadata

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for imputation study.")
    parser.add_argument("--n-rows", type=int, default=1000, help="Number of rows to generate.")
    parser.add_argument("--true-mean", type=float, default=50.0, help="True population mean.")
    parser.add_argument("--true-variance", type=float, default=100.0, help="True population variance.")
    parser.add_argument("--missing-rate", type=float, default=0.2, help="Target missing rate.")
    parser.add_argument("--mechanism", type=str, default="MCAR", choices=["MCAR", "MAR"],
                        help="Missingness mechanism: MCAR or MAR.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--output-csv", type=str, default=None, help="Path to save CSV output.")
    parser.add_argument("--output-meta", type=str, default=None, help="Path to save metadata JSON.")
    parser.add_argument("--schema", type=str, default=None, help="Path to schema file (for validation).")
    parser.add_argument("--generate", action="store_true", help="Run generation.")
    parser.add_argument("--validate-schema", action="store_true", help="Validate output against schema.")

    args = parser.parse_args()

    if not args.generate:
        parser.print_help()
        sys.exit(0)

    ensure_directories()

    # Determine output paths
    if args.output_csv is None:
        base_name = f"synthetic_{args.mechanism.lower()}_v1"
        args.output_csv = f"data/processed/{base_name}.csv"
    if args.output_meta is None:
        base_name = f"synthetic_{args.mechanism.lower()}_v1_meta"
        args.output_meta = f"data/processed/{base_name}.json"

    # Generate data
    df, meta = generate_synthetic_data(
        n=args.n_rows,
        true_mean=args.true_mean,
        true_variance=args.true_variance,
        missing_rate=args.missing_rate,
        mechanism=args.mechanism,
        seed=args.seed
    )

    # Save CSV
    df.to_csv(args.output_csv, index=False)
    logger.info(f"Saved CSV to {args.output_csv}")

    # Save Metadata
    with open(args.output_meta, 'w') as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Saved metadata to {args.output_meta}")

    # Validate if requested
    if args.validate_schema:
        if not validate_schema(df, meta, args.mechanism):
            logger.error("Schema validation failed.")
            sys.exit(1)
        logger.info("Schema validation successful.")

    # Update manifest if needed (optional, handled by update_state.py usually)
    # For now, just print checksums
    csv_path = Path(args.output_csv)
    if csv_path.exists():
        checksum = compute_sha256(csv_path)
        logger.info(f"CSV Checksum: {checksum}")

    logger.info("Synthetic data generation complete.")

if __name__ == "__main__":
    main()