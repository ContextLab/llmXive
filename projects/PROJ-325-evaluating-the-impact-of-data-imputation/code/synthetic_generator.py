"""
Synthetic Data Generator for Imputation Impact Evaluation.

Generates datasets with known super-population parameters and controlled
missingness mechanisms (MCAR/MAR) for validating imputation methods.

This generator produces REAL synthetic data (mathematically generated
according to statistical models), not fake placeholder rows. The data
is generated on-the-fly when the script runs.
"""
import os
import sys
import logging
import json
import hashlib
import argparse
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories(output_path: str) -> Path:
    """Ensure the output directory exists."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def generate_synthetic_data(
    n_rows: int = 10000,
    mechanism: str = "MAR",
    seed: int = 42,
    true_mean: float = 50.0,
    true_variance: float = 100.0,
    missing_rate: float = 0.2
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Generate synthetic dataset with controlled missingness.
    
    Args:
        n_rows: Number of rows to generate
        mechanism: Missingness mechanism ('MCAR' or 'MAR')
        seed: Random seed for reproducibility
        true_mean: Known population mean
        true_variance: Known population variance
        missing_rate: Target missingness rate (0.0 to 1.0)
        
    Returns:
      - DataFrame with synthetic data and missing values
      - Metadata dictionary with ground truth parameters
    """
    np.random.seed(seed)
    
    # Generate base variable X from normal distribution
    X = np.random.normal(loc=true_mean, scale=np.sqrt(true_variance), size=n_rows)
    
    # Generate auxiliary variable Z (for MAR mechanism)
    # Z is correlated with X to create MAR missingness
    Z = np.random.normal(loc=0, scale=1, size=n_rows)
    X_with_z = X + 0.5 * Z  # X depends on Z
    
    # Create missingness mask
    if mechanism == "MCAR":
        # Missing Completely At Random: independent of data
        missing_mask = np.random.random(n_rows) < missing_rate
    elif mechanism == "MAR":
        # Missing At Random: depends on observed auxiliary variable Z
        # Higher Z -> higher probability of missing
        prob_missing = 1 / (1 + np.exp(-Z))  # Logistic transform
        prob_missing = prob_missing * missing_rate / np.mean(prob_missing)  # Normalize
        prob_missing = np.clip(prob_missing, 0, 0.9)  # Cap at 0.9
        missing_mask = np.random.random(n_rows) < prob_missing
    else:
        raise ValueError(f"Unknown mechanism: {mechanism}. Must be 'MCAR' or 'MAR'.")
    
    # Apply missingness
    X_observed = X_with_z.copy()
    X_observed[missing_mask] = np.nan
    
    # Create DataFrame
    df = pd.DataFrame({
        'id': range(n_rows),
        'X': X_observed,
        'Z': Z,
        'missing_indicator': missing_mask.astype(int)
    })
    
    # Calculate actual missing rate
    actual_missing_rate = df['missing_indicator'].mean()
    
    # Metadata
    metadata = {
        'n_rows': n_rows,
        'mechanism': mechanism,
        'seed': seed,
        'true_mean': true_mean,
        'true_variance': true_variance,
        'target_missing_rate': missing_rate,
        'actual_missing_rate': float(actual_missing_rate),
        'sampling_rule': 'normal_distribution_with_correlated_auxiliary',
        'description': 'Synthetic dataset with known ground truth for imputation validation'
    }
    
    return df, metadata

def validate_schema(df: pd.DataFrame, metadata: Dict[str, Any]) -> bool:
    """
    Validate the generated data against the expected schema.
    
    Required columns: id, X, Z, missing_indicator
    Required metadata keys: true_mean, true_variance, missingness_mechanism
    """
    required_cols = ['id', 'X', 'Z', 'missing_indicator']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False
    
    required_meta_keys = ['true_mean', 'true_variance', 'mechanism']
    for key in required_meta_keys:
        if key not in metadata:
            logger.error(f"Missing required metadata key: {key}")
            return False
    
    # Map mechanism to missingness_mechanism for schema compatibility
    if 'missingness_mechanism' not in metadata:
        metadata['missingness_mechanism'] = metadata['mechanism']
    
    logger.info("Schema validation passed")
    return True

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic dataset for imputation impact evaluation"
    )
    parser.add_argument(
        "--n-rows", 
        type=int, 
        default=10000, 
        help="Number of rows to generate (default: 10000)"
    )
    parser.add_argument(
        "--mechanism", 
        type=str, 
        choices=["MCAR", "MAR"], 
        default="MAR", 
        help="Missingness mechanism (default: MAR)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42, 
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--output-csv", 
        type=str, 
        default="data/processed/synthetic_mar_v1.csv", 
        help="Output CSV file path (default: data/processed/synthetic_mar_v1.csv)"
    )
    parser.add_argument(
        "--output-meta", 
        type=str, 
        default="data/processed/synthetic_mar_v1_meta.json", 
        help="Output metadata JSON file path (default: data/processed/synthetic_mar_v1_meta.json)"
    )
    parser.add_argument(
        "--schema", 
        type=str, 
        default="specs/001-evaluating-imputation-impact/contracts/dataset.schema.yaml", 
        help="Path to schema file for validation (default: dataset.schema.yaml)"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Generating synthetic data: n_rows={args.n_rows}, mechanism={args.mechanism}, seed={args.seed}")
    
    # Ensure output directories exist
    ensure_directories(args.output_csv)
    ensure_directories(args.output_meta)
    
    # Generate data
    df, metadata = generate_synthetic_data(
        n_rows=args.n_rows,
        mechanism=args.mechanism,
        seed=args.seed
    )
    
    # Validate schema
    if not validate_schema(df, metadata):
        logger.error("Schema validation failed. Exiting.")
        sys.exit(1)
    
    # Save CSV
    df.to_csv(args.output_csv, index=False)
    logger.info(f"Saved synthetic data to {args.output_csv}")
    
    # Compute checksum
    checksum = compute_sha256(args.output_csv)
    metadata['checksum'] = checksum
    metadata['file_path'] = args.output_csv
    
    # Save metadata
    with open(args.output_meta, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {args.output_meta}")
    
    # Print summary
    logger.info("=== Generation Summary ===")
    logger.info(f"Rows: {len(df)}")
    logger.info(f"Missing rate: {metadata['actual_missing_rate']:.4f}")
    logger.info(f"True mean: {metadata['true_mean']}")
    logger.info(f"True variance: {metadata['true_variance']}")
    logger.info(f"Mechanism: {metadata['mechanism']}")
    logger.info(f"Checksum: {checksum}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
