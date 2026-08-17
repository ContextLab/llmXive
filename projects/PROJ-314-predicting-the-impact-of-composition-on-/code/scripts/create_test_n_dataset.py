"""
Create Test Dataset with Specific Sample Count (N).

This script generates a test dataset with a controlled number of rows
to test data gap validation logic (specifically for N < 30 cases).
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import initialize_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'test_data_generation.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize config
initialize_config()

# Valid compositions as per task T017c
VALID_COMPOSITIONS = [
    'Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO',
    'TiC', 'HfC', 'B4C', 'WC', 'AlN'
]

def generate_test_dataset(num_rows: int = 29, output_path: str = None) -> pd.DataFrame:
    """
    Generate a test dataset with a specific number of rows.

    Args:
        num_rows: Number of rows to generate (default 29 for T017c)
        output_path: Optional path to save the dataset

    Returns:
        Generated DataFrame
    """
    logger.info(f"Generating test dataset with {num_rows} rows...")

    # Cycle through compositions to ensure variety
    compositions = [VALID_COMPOSITIONS[i % len(VALID_COMPOSITIONS)] for i in range(num_rows)]

    # Generate synthetic but realistic values
    # Weibull modulus typically ranges from 2 to 30 for ceramics
    import numpy as np
    np.random.seed(42)  # Reproducibility

    weibull_modulus = np.random.uniform(5.0, 25.0, num_rows)
    sample_count = np.random.randint(30, 100, num_rows)  # N >= 30 for valid entries
    sintering_temp = np.random.uniform(1000.0, 1800.0, num_rows)

    # Primary anion/cation group (derived from composition)
    # Simplified mapping for test data
    def get_group(comp):
        if 'O' in comp: return 'O-Metal'
        if 'N' in comp: return 'N-Metal'
        if 'C' in comp: return 'C-Metal'
        return 'Other'

    primary_groups = [get_group(c) for c in compositions]

    df = pd.DataFrame({
        'composition': compositions,
        'weibull_modulus': weibull_modulus,
        'sample_count': sample_count,
        'sintering_temp': sintering_temp,
        'primary_anion_cation_group': primary_groups
    })

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Test dataset saved to {output_path}")
    else:
        logger.warning("No output path provided; dataset not saved.")

    return df

def main():
    """Main entry point."""
    # Default to 29 rows as per T017c requirement
    num_rows = 29
    output_path = project_root / "data" / "raw" / "test_n.csv"

    logger.info("Starting test dataset generation...")
    df = generate_test_dataset(num_rows=num_rows, output_path=str(output_path))

    # Verify row count
    if len(df) != num_rows:
        logger.error(f"Row count mismatch: expected {num_rows}, got {len(df)}")
        sys.exit(1)

    logger.info(f"Successfully generated {len(df)} rows.")
    sys.exit(0)

if __name__ == "__main__":
    main()
