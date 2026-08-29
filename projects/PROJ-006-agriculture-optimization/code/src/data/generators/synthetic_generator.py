import argparse
import logging
import sys
import os
import random
from pathlib import Path
import pandas as pd
import numpy as np

from src.config.constants import GRID_RESOLUTION_KM, BUFFER_SIZE_KM
from src.utils.io_helpers import write_csv_strict, setup_logging

logger = setup_logging("synthetic_generator")

class SyntheticDataGenerator:
    def __init__(self, seed: int = 42, n_samples: int = 500):
        self.seed = seed
        self.n_samples = n_samples
        random.seed(seed)
        np.random.seed(seed)

    def generate(self) -> pd.DataFrame:
        logger.info(f"Generating {self.n_samples} synthetic records...")

        # Generate household_id
        household_ids = list(range(1, self.n_samples + 1))

        # Generate coordinates (centered around a dummy region, e.g., Malawi)
        # Latitude: -13.0 to -18.0, Longitude: 33.0 to 36.0
        lats = np.random.uniform(-18.0, -13.0, self.n_samples)
        lons = np.random.uniform(33.0, 36.0, self.n_samples)

        # Land size (hectares) - log-normal distribution
        land_sizes = np.random.lognormal(mean=1.5, sigma=1.0, size=self.n_samples)
        land_sizes = np.clip(land_sizes, 0.1, 50.0)

        # Education level (0-10)
        education_levels = np.random.randint(0, 11, self.n_samples)

        # Binary practices
        finance_access = np.random.choice([False, True], size=self.n_samples, p=[0.4, 0.6])
        practice_mixed_farming = np.random.choice([False, True], size=self.n_samples, p=[0.3, 0.7])
        practice_terracing = np.random.choice([False, True], size=self.n_samples, p=[0.2, 0.8])
        practice_conservation_tillage = np.random.choice([False, True], size=self.n_samples, p=[0.25, 0.75])
        practice_agroforestry = np.random.choice([False, True], size=self.n_samples, p=[0.15, 0.85])

        # Extension visits (0-20)
        extension_visits = np.random.randint(0, 21, self.n_samples)

        # HFIAS (Home Food Insecurity Access Scale) - 0 to 30
        hlias = np.random.randint(0, 31, self.n_samples)

        # Construct CSA Index: sum of binary practices (0-4)
        csa_index = (
            practice_mixed_farming.astype(int) +
            practice_terracing.astype(int) +
            practice_conservation_tillage.astype(int) +
            practice_agroforestry.astype(int)
        )

        # Stability Score: Inverse of CV of NDVI (simulated)
        # Simulate NDVI time series variance based on practices
        base_var = 0.05
        # Practices reduce variance
        var_reduction = (
            practice_mixed_farming.astype(int) * 0.01 +
            practice_terracing.astype(int) * 0.015 +
            practice_conservation_tillage.astype(int) * 0.01 +
            practice_agroforestry.astype(int) * 0.02
        )
        total_var = np.maximum(base_var - var_reduction, 0.01)
        # Simulate CV (Coefficient of Variation)
        cvs = np.sqrt(total_var) / (0.5 + np.random.normal(0, 0.05, self.n_samples))
        cvs = np.clip(cvs, 0.01, 1.0)
        stability_scores = 1.0 / cvs
        stability_scores = np.clip(stability_scores, 1.0, 100.0)

        # HFIAS (Food Security): Inverse relationship with CSA and Stability
        # Higher CSA/Stability -> Lower HFIAS
        base_hfias = 25.0
        hfias_adjustment = (
            csa_index * 1.5 +
            (stability_scores / 100.0) * 5.0 +
            (extension_visits * 0.2) -
            (education_levels * 0.5)
        )
        hfiass = base_hfias - hfias_adjustment
        hfiass = np.clip(hfiass, 0, 30).astype(int)

        # Derive village_id by rounding coordinates
        grid_res = GRID_RESOLUTION_KM
        village_lats = np.round(lats / grid_res) * grid_res
        village_lons = np.round(lons / grid_res) * grid_res
        village_ids = [f"V{int(vlat * 100)}_{int(vlon * 100)}" for vlat, vlon in zip(village_lats, village_lons)]

        df = pd.DataFrame({
            "household_id": household_ids,
            "latitude": lats,
            "longitude": lons,
            "land_size": land_sizes,
            "education_level": education_levels,
            "finance_access": finance_access,
            "practice_mixed_farming": practice_mixed_farming,
            "practice_terracing": practice_terracing,
            "practice_conservation_tillage": practice_conservation_tillage,
            "practice_agroforestry": practice_agroforestry,
            "extension_visits": extension_visits,
            "hlias": hlias,
            "CSA_Index": csa_index,
            "Stability_Score": stability_scores,
            "HFIAS": hfiass,
            "village_id": village_ids
        })

        return df

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for pipeline testing")
    parser.add_argument("--output", type=str, default="data/processed/analysis_dataset.csv", help="Output file path")
    parser.add_argument("--n-samples", type=int, default=500, help="Number of samples to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generator = SyntheticDataGenerator(seed=args.seed, n_samples=args.n_samples)
    df = generator.generate()

    logger.info(f"Writing dataset to {output_path}")
    write_csv_strict(df, output_path)
    logger.info("Synthetic data generation complete.")

if __name__ == "__main__":
    main()
