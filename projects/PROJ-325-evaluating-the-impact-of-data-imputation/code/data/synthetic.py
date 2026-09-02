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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_directories(file_path: str) -> Path:
    """Ensure the directory for the given file path exists."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.parent

def validate_schema(data: Dict[str, Any], schema_path: str) -> bool:
    """
    Validate the generated data against the dataset schema.
    For this implementation, we perform a structural check since
    we don't have a JSON schema validator library installed by default.
    """
    required_fields = ['true_mean', 'true_variance', 'missingness_mechanism', 'n', 'missing_rate']
    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field in metadata: {field}")
            return False
    
    # Type checks
    if not isinstance(data['true_mean'], (int, float)):
        logger.error("true_mean must be a number")
        return False
    if not isinstance(data['true_variance'], (int, float)):
        logger.error("true_variance must be a number")
        return False
    if data['missingness_mechanism'] not in ['MCAR', 'MAR']:
        logger.error("missingness_mechanism must be MCAR or MAR")
        return False
    if not isinstance(data['n'], int) or data['n'] <= 0:
        logger.error("n must be a positive integer")
        return False
    if not isinstance(data['missing_rate'], (int, float)) or not (0 <= data['missing_rate'] <= 1):
        logger.error("missing_rate must be between 0 and 1")
        return False

    logger.info("Schema validation passed.")
    return True

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_synthetic_data(
    n: int = 1000,
    true_mean: float = 50.0,
    true_variance: float = 100.0,
    missing_rate: float = 0.2,
    mechanism: str = 'MAR',
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates synthetic data with specified super-population parameters.
    
    Args:
        n: Number of samples
        true_mean: Population mean
        true_variance: Population variance
        missing_rate: Fraction of missing values to introduce
        mechanism: 'MCAR' or 'MAR'
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with synthetic data and missing values
    """
    np.random.seed(seed)
    
    # Generate base data
    # We generate X ~ N(mean, variance)
    data = np.random.normal(loc=true_mean, scale=np.sqrt(true_variance), size=n)
    
    df = pd.DataFrame({'value': data})
    
    # Introduce missingness
    if mechanism == 'MCAR':
        # Missing Completely At Random: independent of data values
        mask = np.random.random(n) < missing_rate
    elif mechanism == 'MAR':
        # Missing At Random: depends on observed values (here, value itself)
        # Higher values are more likely to be missing
        probs = missing_rate + 0.1 * (df['value'] - true_mean) / np.sqrt(true_variance)
        probs = np.clip(probs, 0, 1)
        mask = np.random.random(n) < probs
    else:
        raise ValueError(f"Unknown mechanism: {mechanism}")
    
    df.loc[mask, 'value'] = np.nan
    
    # Add metadata columns for validation
    df['true_mean'] = true_mean
    df['true_variance'] = true_variance
    df['missingness_mechanism'] = mechanism
    df['missing_rate'] = missing_rate
    df['n'] = n
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for imputation study")
    parser.add_argument('--n-rows', type=int, default=1000, help='Number of rows to generate')
    parser.add_argument('--true-mean', type=float, default=50.0, help='True population mean')
    parser.add_argument('--true-variance', type=float, default=100.0, help='True population variance')
    parser.add_argument('--missing-rate', type=float, default=0.2, help='Missing rate (0-1)')
    parser.add_argument('--mechanism', type=str, default='MAR', choices=['MCAR', 'MAR'], 
                        help='Missingness mechanism')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output-csv', type=str, default='data/processed/synthetic_mar_v1.csv',
                        help='Output CSV file path')
    parser.add_argument('--output-meta', type=str, default='data/processed/synthetic_mar_v1_meta.json',
                        help='Output metadata JSON file path')
    parser.add_argument('--schema', type=str, default='specs/001-evaluating-the-impact-of-data-imputation/contracts/dataset.schema.yaml',
                        help='Path to schema file for validation')
    
    args = parser.parse_args()
    
    # Ensure output directories exist
    ensure_directories(args.output_csv)
    ensure_directories(args.output_meta)
    
    logger.info(f"Generating synthetic data: n={args.n_rows}, mean={args.true_mean}, "
                f"var={args.true_variance}, miss_rate={args.missing_rate}, mech={args.mechanism}")
    
    # Generate data
    df = generate_synthetic_data(
        n=args.n_rows,
        true_mean=args.true_mean,
        true_variance=args.true_variance,
        missing_rate=args.missing_rate,
        mechanism=args.mechanism,
        seed=args.seed
    )
    
    # Save CSV
    df.to_csv(args.output_csv, index=False)
    logger.info(f"Saved synthetic data to {args.output_csv}")
    
    # Create metadata
    metadata = {
        'true_mean': args.true_mean,
        'true_variance': args.true_variance,
        'missingness_mechanism': args.mechanism,
        'n': args.n_rows,
        'missing_rate': args.missing_rate,
        'seed': args.seed,
        'output_file': args.output_csv
    }
    
    # Validate metadata against schema
    if validate_schema(metadata, args.schema):
        # Save metadata
        with open(args.output_meta, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {args.output_meta}")
        
        # Compute and log checksum
        checksum = compute_sha256(args.output_csv)
        logger.info(f"SHA-256 checksum of {args.output_csv}: {checksum}")
        
        # Update manifest (if update_state module is available)
        try:
            from update_state import compute_file_hash, find_artifacts, generate_manifest, update_manifest, main as update_main
            # We will just log the hash here; the manifest update is handled by T007
            logger.info("Artifact generated successfully. Run update_state.py to record in manifest.")
        except ImportError:
            logger.warning("update_state module not found. Skipping manifest update.")
    else:
        logger.error("Schema validation failed. Aborting.")
        sys.exit(1)

if __name__ == '__main__':
    main()
