import os
import logging
import pandas as pd
import numpy as np
import hashlib
import json
from typing import List, Dict, Any, Optional

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
    Compute MD5 checksum of the row dictionary.

    The checksum is the MD5 hash of the JSON representation of the row dictionary,
    with keys sorted alphabetically and no whitespace, encoded as UTF-8.
    This ensures deterministic output across environments.

    Args:
        row: Dictionary containing row data.

    Returns:
        Hexadecimal string of the MD5 hash.
    """
    # Create a copy to avoid modifying the original
    row_copy = row.copy()

    # Round all float values to 15 decimal places to ensure deterministic checksums
    # across Python versions and floating point representations
    for key, value in row_copy.items():
        if isinstance(value, float):
            row_copy[key] = round(value, 15)

    # Create JSON string with sorted keys and no whitespace
    json_str = json.dumps(row_copy, sort_keys=True, separators=(',', ':'))
    # Encode to UTF-8 and compute MD5
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()

def generate_validation_dataset(output_path: str, seed: int = 42) -> None:
    """
    Generate a small sample dataset for manual verification.

    This script generates data for a specific set of configurations (small sample sizes)
    across different distributions and effect sizes, calculates statistics,
    validates them against theoretical expectations, and saves the results to a CSV.

    Args:
        output_path: Path to save the output CSV file.
        seed: Random seed for reproducibility.
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

        try:
            # Generate data using the data_generator module
            # Use a unique seed for each scenario to ensure independence
            scenario_seed = seed + (n * 100) + (int(dist_type == "uniform") * 50) + (int(dist_type == "log_normal") * 30) + int(effect_size * 10)
            
            # Call generate_data with positional arguments matching the defined API
            # The API surface shows: generate_data(n, dist, eff, seed=seed)
            data_dict = generate_data(n, dist_type, effect_size, seed=scenario_seed)
            
            group1 = data_dict['group1']
            group2 = data_dict['group2']
            stats = data_dict['stats']
            
            # Validate statistics - this raises an error if validation fails
            # This ensures the generated data matches theoretical expectations
            validate_sample_statistics(group1, group2, effect_size, dist_type)
            
            # Calculate metrics for the CSV
            group_mean_1 = float(np.mean(group1))
            group_mean_2 = float(np.mean(group2))
            mean_diff = group_mean_2 - group_mean_1
            # Calculate variance of the combined data (ddof=1 for sample variance)
            variance = float(np.var(np.concatenate([group1, group2]), ddof=1))
            skewness = float(stats['skewness'])
            
            # Prepare row data
            row_data = {
                "sample_size": n,
                "distribution_type": dist_type,
                "effect_size": float(effect_size),
                "group_mean_1": group_mean_1,
                "group_mean_2": group_mean_2,
                "mean_diff": mean_diff,
                "variance": variance,
                "skewness": skewness,
                "checksum": ""  # Placeholder to be filled
            }
            
            # Compute checksum using the updated method
            row_data["checksum"] = compute_row_checksum(row_data)
            
            results.append(row_data)
            logger.info(f"  -> Generated successfully. Mean diff: {mean_diff:.6f}, Checksum: {row_data['checksum'][:8]}...")

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