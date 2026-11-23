import argparse
import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_directories(path: str) -> None:
    """Ensure the directory for the given path exists."""
    dir_path = Path(path).parent
    dir_path.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_schema(data: Dict[str, Any], schema_path: str = "contracts/dataset.schema.yaml") -> bool:
    """
    Validate data against the JSON schema.
    For this task, we perform a simplified validation based on the schema definition.
    """
    required_fields = ["true_mean", "true_variance", "missingness_mechanism", "n", "missing_rate"]
    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field in metadata: {field}")
            return False
    
    if not isinstance(data["true_mean"], (int, float)):
        logger.error("true_mean must be a number")
        return False
    if not isinstance(data["true_variance"], (int, float)):
        logger.error("true_variance must be a number")
        return False
    if data["missingness_mechanism"] not in ["MCAR", "MAR"]:
        logger.error("missingness_mechanism must be 'MCAR' or 'MAR'")
        return False
    if not isinstance(data["n"], int):
        logger.error("n must be an integer")
        return False
    if not isinstance(data["missing_rate"], (int, float)):
        logger.error("missing_rate must be a number")
        return False

    return True

def generate_synthetic_data(
    n: int = 1000,
    true_mean: float = 50.0,
    true_variance: float = 100.0,
    missing_rate: float = 0.2,
    mechanism: str = "MCAR",
    seed: int = 42,
    output_csv: Optional[str] = None,
    output_meta: Optional[str] = None
) -> pd.DataFrame:
    """
    Generate synthetic dataset with known super-population parameters.
    
    Args:
        n: Number of rows.
        true_mean: Mean of the population.
        true_variance: Variance of the population.
        missing_rate: Proportion of data to mask.
        mechanism: 'MCAR' or 'MAR'.
        seed: Random seed for reproducibility.
        output_csv: Path to save the CSV file.
        output_meta: Path to save the metadata JSON file.
    
    Returns:
        DataFrame containing the synthetic dataset.
    """
    np.random.seed(seed)
    
    # Generate base data
    data = np.random.normal(loc=true_mean, scale=np.sqrt(true_variance), size=n)
    df = pd.DataFrame({"value": data})
    
    # Generate missingness mask
    if mechanism == "MCAR":
        # Random mask independent of data
        mask = np.random.random(n) < missing_rate
    elif mechanism == "MAR":
        # Logistic probability mask based on observed covariates
        # Here we use the value itself (or a transformed version) to determine missingness
        # For simplicity, we use the value to create a probability
        # Higher values -> higher chance of missing (or vice versa)
        prob = 1 / (1 + np.exp(-(data - true_mean) / (np.sqrt(true_variance) * 0.5)))
        # Scale prob to match missing_rate roughly, but ensure variation
        # We want average probability to be close to missing_rate
        prob = prob * (missing_rate / np.mean(prob))
        prob = np.clip(prob, 0, 1)
        mask = np.random.random(n) < prob
    else:
        raise ValueError(f"Unknown mechanism: {mechanism}")
    
    # Apply mask
    df["value_masked"] = df["value"].copy()
    df.loc[mask, "value_masked"] = np.nan
    df["is_missing"] = mask
    
    # Prepare metadata
    metadata = {
        "true_mean": true_mean,
        "true_variance": true_variance,
        "missingness_mechanism": mechanism,
        "n": n,
        "missing_rate": missing_rate,
        "seed": seed
    }
    
    # Validate metadata against schema
    if not validate_schema(metadata):
        logger.error("Metadata validation failed.")
        sys.exit(1)
    
    # Save outputs if paths provided
    if output_csv:
        ensure_directories(output_csv)
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved synthetic data to {output_csv}")
    
    if output_meta:
        ensure_directories(output_meta)
        with open(output_meta, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {output_meta}")
    
    return df

def generate_synthetic_data_mcar(
    n: int = 1000,
    true_mean: float = 50.0,
    true_variance: float = 100.0,
    missing_rate: float = 0.2,
    seed: int = 42,
    output_csv: Optional[str] = None,
    output_meta: Optional[str] = None
) -> pd.DataFrame:
    """
    Generate synthetic dataset with MCAR mechanism.
    This is a specific configuration of generate_synthetic_data.
    
    Args:
        n: Number of rows.
        true_mean: Mean of the population.
        true_variance: Variance of the population.
        missing_rate: Proportion of data to mask.
        seed: Random seed for reproducibility.
        output_csv: Path to save the CSV file.
        output_meta: Path to save the metadata JSON file.
    
    Returns:
        DataFrame containing the synthetic dataset.
    """
    return generate_synthetic_data(
        n=n,
        true_mean=true_mean,
        true_variance=true_variance,
        missing_rate=missing_rate,
        mechanism="MCAR",
        seed=seed,
        output_csv=output_csv,
        output_meta=output_meta
    )

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for imputation studies.")
    parser.add_argument("--generate", action="store_true", help="Generate synthetic data.")
    parser.add_argument("--validate-schema", action="store_true", help="Validate output against schema.")
    parser.add_argument("--n-rows", type=int, default=1000, help="Number of rows to generate.")
    parser.add_argument("--true-mean", type=float, default=50.0, help="True mean of the population.")
    parser.add_argument("--true-variance", type=float, default=100.0, help="True variance of the population.")
    parser.add_argument("--missing-rate", type=float, default=0.2, help="Missing rate.")
    parser.add_argument("--mechanism", type=str, choices=["MCAR", "MAR"], default="MCAR", help="Missingness mechanism.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--output-csv", type=str, help="Path to save the CSV file.")
    parser.add_argument("--output-meta", type=str, help="Path to save the metadata JSON file.")
    parser.add_argument("--schema", type=str, default="contracts/dataset.schema.yaml", help="Path to schema file.")

    args = parser.parse_args()

    if args.generate:
        logger.info(f"Generating synthetic data with mechanism={args.mechanism}, n={args.n_rows}")
        
        # Determine output paths if not provided
        if not args.output_csv:
            args.output_csv = f"data/processed/synthetic_{args.mechanism.lower()}_v1.csv"
        if not args.output_meta:
            args.output_meta = f"data/processed/synthetic_{args.mechanism.lower()}_v1_meta.json"
        
        # Generate data
        df = generate_synthetic_data(
            n=args.n_rows,
            true_mean=args.true_mean,
            true_variance=args.true_variance,
            missing_rate=args.missing_rate,
            mechanism=args.mechanism,
            seed=args.seed,
            output_csv=args.output_csv,
            output_meta=args.output_meta
        )
        
        # Compute checksum
        if os.path.exists(args.output_csv):
            checksum = compute_sha256(args.output_csv)
            logger.info(f"Checksum for {args.output_csv}: {checksum}")
        
        if args.validate_schema:
            with open(args.output_meta, "r") as f:
                metadata = json.load(f)
            if validate_schema(metadata, args.schema):
                logger.info("Schema validation passed.")
            else:
                logger.error("Schema validation failed.")
                sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
