import os
import logging
import pandas as pd
import numpy as np
import hashlib
from typing import List, Dict, Any

from data_generator import generate_data, validate_sample_statistics
from config import SimulationConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_row_checksum(row: Dict[str, Any]) -> str:
    """
    Compute MD5 checksum of the row data.
    The checksum is calculated over the string representation of the key-value pairs
    to ensure consistency and detect data tampering.
    """
    # Sort keys to ensure deterministic order
    sorted_items = sorted(row.items())
    # Create a string representation
    data_str = "|".join([f"{k}={v}" for k, v in sorted_items])
    return hashlib.md5(data_str.encode('utf-8')).hexdigest()

def generate_validation_dataset(output_path: str) -> None:
    """
    Generate a small sample dataset for manual verification.
    
    This script generates data for a specific set of configurations (small sample sizes)
    across different distributions and effect sizes, calculates statistics,
    validates them against theoretical expectations, and saves the results to a CSV.
    
    Args:
        output_path: Path to save the output CSV file.
    """
    # Define a small set of scenarios for validation
    # We use small sample sizes to make manual verification feasible
    scenarios = [
        {"n": 10, "dist": "normal", "effect": 0.0},
        {"n": 10, "dist": "normal", "effect": 0.5},
        {"n": 20, "dist": "normal", "effect": 0.0},
        {"n": 20, "dist": "normal", "effect": 0.5},
        {"n": 50, "dist": "uniform", "effect": 0.0},
        {"n": 50, "dist": "uniform", "effect": 0.5},
        {"n": 30, "dist": "log_normal", "effect": 0.0},
        {"n": 30, "dist": "log_normal", "effect": 0.5},
    ]

    results = []

    for scenario in scenarios:
        n = scenario["n"]
        dist_type = scenario["dist"]
        effect_size = scenario["effect"]

        logger.info(f"Generating scenario: n={n}, dist={dist_type}, effect={effect_size}")

        # Generate data
        # Note: generate_data returns a dict with 'group1', 'group2', 'stats'
        # We assume the config is set up with standard parameters (mu=0, sigma=1 for normal/uniform)
        # and effect_size is applied to the mean of group2.
        
        # We need to construct a config object or pass parameters directly.
        # Looking at data_generator API, it likely takes params.
        # Let's assume standard params: mu=0, sigma=1, scale=1 (for lognormal)
        
        try:
            data_dict = generate_data(
                sample_size=n,
                distribution_type=dist_type,
                effect_size=effect_size,
                seed=42  # Fixed seed for reproducibility
            )
            
            group1 = data_dict['group1']
            group2 = data_dict['group2']
            stats = data_dict['stats']
            
            # Validate statistics
            # This function raises an error if validation fails
            validate_sample_statistics(group1, group2, effect_size, dist_type)
            
            # Calculate metrics for the CSV
            group_mean_1 = float(np.mean(group1))
            group_mean_2 = float(np.mean(group2))
            mean_diff = group_mean_2 - group_mean_1
            variance = float(np.var(np.concatenate([group1, group2]), ddof=1))
            skewness = float(stats['skewness'])
            
            row_data = {
                "sample_size": n,
                "distribution_type": dist_type,
                "effect_size": effect_size,
                "group_mean_1": group_mean_1,
                "group_mean_2": group_mean_2,
                "mean_diff": mean_diff,
                "variance": variance,
                "skewness": skewness,
                "checksum": "" # Placeholder
            }
            
            # Compute checksum
            row_data["checksum"] = compute_row_checksum(row_data)
            
            results.append(row_data)
            logger.info(f"  -> Generated successfully. Mean diff: {mean_diff:.6f}")

        except Exception as e:
            logger.error(f"  -> Failed for scenario {scenario}: {str(e)}")
            raise

    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Validation dataset saved to {output_path}")

def main():
    """Main entry point for the validation data generation script."""
    output_path = "data/raw/sample_validation.csv"
    generate_validation_dataset(output_path)

if __name__ == "__main__":
    main()
