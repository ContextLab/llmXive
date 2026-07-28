"""
Synthetic Data Generator for Imputation Impact Evaluation.

This module generates synthetic datasets with known super-population parameters
(true_mean, true_variance) and controlled missingness mechanisms (MCAR, MAR).

The generated data conforms to the dataset schema defined in 
specs/001-evaluating-the-impact-of-data-imputation/contracts/dataset.schema.yaml.

Outputs:
  - data/processed/synthetic_mar_v1.csv: The synthetic dataset.
  - data/processed/synthetic_mar_v1_meta.json: Metadata containing ground truth.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

# Import from project config to ensure consistent seed management
# Note: Using config.py directly to avoid circular imports if synthetic.py is imported elsewhere
from config import SeedManager, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ensure_directories(output_path: Path) -> None:
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)


def generate_synthetic_data(
    n: int,
    true_mean: float,
    true_variance: float,
    missing_rate: float,
    mechanism: str,
    seed: int,
    design_cols: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Generate a synthetic dataset with known parameters and missingness.
    
    Args:
        n: Number of rows to generate.
        true_mean: The known population mean for the target variable.
        true_variance: The known population variance for the target variable.
        missing_rate: Proportion of missing values to introduce (0.0 to 1.0).
        mechanism: The missingness mechanism ('MCAR' or 'MAR').
        seed: Random seed for reproducibility.
        design_cols: Optional dictionary containing design columns (weight, psu, strata).
                     If None, dummy design columns are generated.
                     
    Returns:
        A pandas DataFrame containing the synthetic data.
        
    Raises:
        ValueError: If mechanism is not supported or parameters are invalid.
    """
    if mechanism not in ['MCAR', 'MAR']:
        raise ValueError(f"Unsupported mechanism: {mechanism}. Must be 'MCAR' or 'MAR'.")
        
    np.random.seed(seed)
    
    # Calculate standard deviation
    std_dev = np.sqrt(true_variance)
    
    # Generate the target variable (e.g., 'income')
    # Using a normal distribution for simplicity, though real data might be skewed.
    # We ensure the sample statistics are close to population parameters.
    data = np.random.normal(loc=true_mean, scale=std_dev, size=n)
    
    df = pd.DataFrame({
        'income': data
    })
    
    # Add design columns if not provided, or use provided ones
    if design_cols is None:
        # Generate dummy design columns
        df['weight'] = np.random.uniform(0.5, 2.0, size=n)
        df['psu'] = np.random.randint(1, 50, size=n)
        df['strata'] = np.random.randint(1, 10, size=n)
    else:
        # Validate and add provided design columns
        for col_name, col_data in design_cols.items():
            if len(col_data) != n:
                raise ValueError(f"Design column '{col_name}' length mismatch.")
            df[col_name] = col_data
        
    # Introduce missingness
    if missing_rate > 0:
        if mechanism == 'MCAR':
            # Missing Completely At Random: random selection of rows
            missing_mask = np.random.random(n) < missing_rate
        elif mechanism == 'MAR':
            # Missing At Random: missingness depends on another observed variable
            # For example, missingness depends on 'weight' (higher weight -> higher chance of missing)
            # Normalize weight to 0-1 range for probability calculation
            weights = df['weight'].values
            # Shift and scale to ensure probabilities are valid
            # P(missing) = missing_rate + 0.1 * (weight - mean_weight) / std_weight
            # Clamp to [0, 1]
            prob_missing = missing_rate + 0.2 * (weights - np.mean(weights)) / (np.std(weights) + 1e-8)
            prob_missing = np.clip(prob_missing, 0, 1)
            missing_mask = np.random.random(n) < prob_missing
        
        df.loc[missing_mask, 'income'] = np.nan
        logger.info(f"Introduced {missing_mask.sum()} missing values ({missing_mask.mean()*100:.2f}%) via {mechanism}.")
    else:
        logger.info("No missing values introduced.")
        
    return df


def validate_schema(df: pd.DataFrame, schema_path: Optional[str] = None) -> bool:
    """
    Validate the generated DataFrame against the expected schema.
    
    Args:
        df: The DataFrame to validate.
        schema_path: Path to the schema file (optional, for future extensibility).
        
    Returns:
        True if valid, False otherwise.
    """
    required_columns = ['income', 'weight', 'psu', 'strata']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
        
    # Check for non-negative weights
    if (df['weight'] <= 0).any():
        logger.warning("Warning: Negative or zero weights detected.")
        
    # Check for integer-like psu and strata
    if not np.issubdtype(df['psu'].dtype, np.integer):
        logger.warning("Warning: PSU column is not integer type.")
    if not np.issubdtype(df['strata'].dtype, np.integer):
        logger.warning("Warning: Strata column is not integer type.")
        
    logger.info("Schema validation passed.")
    return True


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    """Main entry point for the synthetic data generator."""
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for imputation studies.")
    parser.add_argument('--n-rows', type=int, default=50000, help='Number of rows to generate.')
    parser.add_argument('--true-mean', type=float, default=50000.0, help='True population mean.')
    parser.add_argument('--true-variance', type=float, default=25000000.0, help='True population variance.')
    parser.add_argument('--missing-rate', type=float, default=0.15, help='Proportion of missing values.')
    parser.add_argument('--mechanism', type=str, choices=['MCAR', 'MAR'], default='MAR', help='Missingness mechanism.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed.')
    parser.add_argument('--output-csv', type=str, default='data/processed/synthetic_mar_v1.csv', help='Output CSV path.')
    parser.add_argument('--output-meta', type=str, default='data/processed/synthetic_mar_v1_meta.json', help='Output metadata JSON path.')
    
    args = parser.parse_args()
    
    logger.info(f"Starting synthetic data generation with seed={args.seed}, n={args.n_rows}, mechanism={args.mechanism}")
    
    # Ensure output directories exist
    ensure_directories(Path(args.output_csv))
    ensure_directories(Path(args.output_meta))
    
    # Generate data
    df = generate_synthetic_data(
        n=args.n_rows,
        true_mean=args.true_mean,
        true_variance=args.true_variance,
        missing_rate=args.missing_rate,
        mechanism=args.mechanism,
        seed=args.seed
    )
    
    # Validate schema
    if not validate_schema(df):
        logger.error("Schema validation failed. Aborting.")
        sys.exit(1)
        
    # Save CSV
    df.to_csv(args.output_csv, index=False)
    logger.info(f"Saved synthetic data to {args.output_csv}")
    
    # Compute checksum
    checksum = compute_sha256(Path(args.output_csv))
    
    # Prepare metadata
    metadata = {
        "true_mean": args.true_mean,
        "true_variance": args.true_variance,
        "missingness_mechanism": args.mechanism,
        "missing_rate": args.missing_rate,
        "n_rows": args.n_rows,
        "seed": args.seed,
        "file_checksum": checksum,
        "file_path": args.output_csv,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Save metadata
    with open(args.output_meta, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {args.output_meta}")
    
    logger.info("Synthetic data generation completed successfully.")


if __name__ == "__main__":
    main()