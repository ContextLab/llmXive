import argparse
import logging
import sys
import os
import random
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
import numpy as np

# Import the fixed logging setup from io_helpers
from src.utils.io_helpers import setup_logging, write_csv_strict

logger = setup_logging("synthetic_generator")

class SyntheticDataGenerator:
    """Generates synthetic survey data for structural validation."""

    def __init__(self, seed: int = 42, n_samples: int = 1000):
        self.seed = seed
        self.n_samples = n_samples
        random.seed(seed)
        np.random.seed(seed)

    def generate(self) -> pd.DataFrame:
        """Generate synthetic dataset."""
        logger.info(f"Generating {self.n_samples} synthetic records with seed {self.seed}")

        # Base IDs
        household_ids = list(range(1, self.n_samples + 1))
        village_ids = [f"V{random.randint(1, 50)}" for _ in range(self.n_samples)]

        # Coordinates (random lat/lon in a plausible region, e.g., East Africa)
        lats = np.random.uniform(-2.0, 2.0, self.n_samples)
        lons = np.random.uniform(30.0, 36.0, self.n_samples)

        # Land size (hectares)
        land_sizes = np.random.exponential(scale=2.0, size=self.n_samples)
        land_sizes = np.clip(land_sizes, 0.1, 20.0)

        # Education level (1-5)
        education_levels = np.random.randint(1, 6, self.n_samples)

        # Finance access (bool)
        finance_access = np.random.choice([True, False], self.n_samples, p=[0.4, 0.6])

        # Practices (binary)
        practice_mixed = np.random.choice([True, False], self.n_samples, p=[0.3, 0.7])
        practice_terracing = np.random.choice([True, False], self.n_samples, p=[0.2, 0.8])
        practice_conservation = np.random.choice([True, False], self.n_samples, p=[0.25, 0.75])
        practice_agroforestry = np.random.choice([True, False], self.n_samples, p=[0.15, 0.85])

        # Extension visits
        extension_visits = np.random.poisson(lam=2, size=self.n_samples)

        # Derived metrics
        # CSA Index: Sum of practices + weighted extension visits
        csa_index = (
            practice_mixed.astype(int) +
            practice_terracing.astype(int) +
            practice_conservation.astype(int) +
            practice_agroforestry.astype(int) +
            (extension_visits * 0.5)
        )

        # Stability Score (simulated as 1/CV of NDVI, here simulated directly)
        # Simulate a base stability and add noise
        stability_base = 10.0 + (csa_index * 0.5)
        stability_score = stability_base + np.random.normal(0, 2.0, self.n_samples)
        stability_score = np.clip(stability_score, 0.1, 20.0)

        # HFIAS (Food Insecurity) - inverse relationship with stability/CSA roughly
        hlias = np.random.normal(loc=15.0 - (csa_index * 1.5), scale=3.0, size=self.n_samples)
        hlias = np.clip(hlias, 0, 30)

        df = pd.DataFrame({
            'household_id': household_ids,
            'latitude': lats,
            'longitude': lons,
            'land_size': land_sizes,
            'education_level': education_levels,
            'finance_access': finance_access,
            'practice_mixed_farming': practice_mixed,
            'practice_terracing': practice_terracing,
            'practice_conservation_tillage': practice_conservation,
            'practice_agroforestry': practice_agroforestry,
            'extension_visits': extension_visits,
            'hlias': hlias.astype(int),
            'CSA_Index': csa_index,
            'Stability_Score': stability_score,
            'HFIAS': hlias,
            'village_id': village_ids
        })

        return df

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for structural validation.")
    parser.add_argument("--output", type=str, default="data/raw/synthetic_survey.csv",
                        help="Output file path")
    parser.add_argument("--n-samples", type=int, default=1000,
                        help="Number of samples to generate")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    args = parser.parse_args()

    generator = SyntheticDataGenerator(seed=args.seed, n_samples=args.n_samples)
    df = generator.generate()

    output_path = Path(args.output)
    write_csv_strict(df, output_path)
    logger.info(f"Successfully wrote synthetic data to {output_path}")

if __name__ == "__main__":
    main()
