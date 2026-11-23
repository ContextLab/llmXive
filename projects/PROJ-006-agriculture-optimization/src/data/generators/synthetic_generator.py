"""
Synthetic Data Generator.

Generates a statistically realistic dataset for CI validation and local testing.
Uses Multivariate Normal for continuous variables and Bernoulli for binary variables.
"""

import argparse
import logging
import sys
import os
import random
from pathlib import Path

import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.io_helpers import setup_logging, write_csv_strict
from src.config.constants import RANDOM_SEED

logger = setup_logging("synthetic_generator")

class SyntheticDataGenerator:
    def __init__(self, n_rows: int = 500, seed: int = RANDOM_SEED):
        self.n_rows = n_rows
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def generate(self) -> pd.DataFrame:
        """Generate the synthetic dataset."""
        logger.info(f"Generating {self.n_rows} synthetic records.")

        # 1. household_id
        household_ids = list(range(1, self.n_rows + 1))

        # 2. latitude, longitude (Centered around Malawi/Tanzania region)
        # Malawi approx: -13.5, 34.0
        # Tanzania approx: -6.0, 35.0
        # We'll generate a cluster around a point in Malawi
        lats = np.random.normal(loc=-13.5, scale=2.0, size=self.n_rows)
        lons = np.random.normal(loc=34.0, scale=2.0, size=self.n_rows)

        # 3. land_size (hectares) - Log-normal distribution
        land_sizes = np.random.lognormal(mean=1.0, sigma=0.5, size=self.n_rows)

        # 4. education_level (0-10)
        education_levels = np.random.randint(0, 11, size=self.n_rows)

        # 5. finance_access (bool)
        finance_access = np.random.choice([True, False], size=self.n_rows, p=[0.4, 0.6])

        # 6. Practice indicators (bool)
        practice_mixed_farming = np.random.choice([True, False], size=self.n_rows, p=[0.5, 0.5])
        practice_terracing = np.random.choice([True, False], size=self.n_rows, p=[0.3, 0.7])
        practice_conservation_tillage = np.random.choice([True, False], size=self.n_rows, p=[0.4, 0.6])
        practice_agroforestry = np.random.choice([True, False], size=self.n_rows, p=[0.35, 0.65])

        # 7. extension_visits (int)
        extension_visits = np.random.poisson(lam=2, size=self.n_rows)

        # 8. hlias (int) - Household Food Insecurity Access Scale (0-24)
        hlias = np.random.randint(0, 25, size=self.n_rows)

        # 9. CSA_Index (float) - Sum of practice indicators (0-4)
        csa_index = (practice_mixed_farming.astype(int) + 
                     practice_terracing.astype(int) + 
                     practice_conservation_tillage.astype(int) + 
                     practice_agroforestry.astype(int))

        # 10. Stability_Score (float) - Derived from simulated NDVI stability
        # Simulate a score between 0 and 1
        stability_scores = np.random.beta(a=2, b=5, size=self.n_rows)

        # 11. HFIAS (float) - Household Food Insecurity Access Scale (continuous version)
        hfias = hlias.astype(float) + np.random.normal(0, 0.5, size=self.n_rows)
        hfias = np.clip(hfias, 0, 24)

        # 12. village_id - Derived from rounded coordinates
        grid_res = 0.1
        village_lats = np.round(lats / grid_res) * grid_res
        village_lons = np.round(lons / grid_res) * grid_res
        village_ids = [f"V_{int(lat)}_{int(lon)}" for lat, lon in zip(village_lats, village_lons)]

        df = pd.DataFrame({
            'household_id': household_ids,
            'latitude': lats,
            'longitude': lons,
            'land_size': land_sizes,
            'education_level': education_levels,
            'finance_access': finance_access,
            'practice_mixed_farming': practice_mixed_farming,
            'practice_terracing': practice_terracing,
            'practice_conservation_tillage': practice_conservation_tillage,
            'practice_agroforestry': practice_agroforestry,
            'extension_visits': extension_visits,
            'hlias': hlias,
            'CSA_Index': csa_index,
            'Stability_Score': stability_scores,
            'HFIAS': hfias,
            'village_id': village_ids
        })

        return df

    def save(self, output_path: Path):
        """Save the generated dataframe to CSV."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = self.generate()
        write_csv_strict(df, output_path)
        logger.info(f"Synthetic data saved to {output_path}")
        return df

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for pipeline testing")
    parser.add_argument("--output", 
                        type=str, 
                        default="data/raw/synthetic_survey.csv",
                        help="Output path for synthetic data")
    parser.add_argument("--n-rows", 
                        type=int, 
                        default=500,
                        help="Number of rows to generate")
    args = parser.parse_args()

    output_path = project_root / args.output
    
    try:
        generator = SyntheticDataGenerator(n_rows=args.n_rows)
        generator.save(output_path)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()