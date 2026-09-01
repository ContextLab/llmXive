"""
Synthetic Data Generator for CI validation and local testing fallback.
Generates statistically realistic datasets matching the project schema.
"""
import argparse
import logging
import sys
import os
import random
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd

# Import local utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.io_helpers import setup_logging, write_csv_strict, FatalError


# Configuration
NUM_HOUSEHOLDS = 1200  # Ensure > 300 requirement
SEED = 42
COUNTRIES = ["Malawi", "Tanzania"]
REGIONS = {
    "Malawi": ["Central", "Southern", "Northern"],
    "Tanzania": ["Mainland", "Zanzibar"]
}


class SyntheticDataGenerator:
    """Generates synthetic household and agricultural practice data."""

    def __init__(self, seed: int = SEED, logger: logging.Logger = None):
        self.seed = seed
        self.logger = logger or setup_logging("synthetic_generator", "INFO")
        random.seed(seed)
        np.random.seed(seed)

    def generate_household_id(self, n: int) -> List[int]:
        """Generate unique household IDs."""
        return list(range(10000, 10000 + n))

    def generate_coordinates(self, n: int, country: str) -> Dict[str, np.ndarray]:
        """Generate realistic latitude/longitude based on country."""
        if country == "Malawi":
            # Approx bounds for Malawi
            lats = np.random.uniform(-17.2, -9.2, n)
            lons = np.random.uniform(32.6, 35.9, n)
        else:
            # Approx bounds for Tanzania
            lats = np.random.uniform(-11.7, -1.0, n)
            lons = np.random.uniform(29.3, 40.4, n)
        return {"latitude": lats, "longitude": lons}

    def generate_land_size(self, n: int) -> np.ndarray:
        """Generate land size in hectares (log-normal distribution)."""
        return np.random.lognormal(mean=0.5, sigma=0.8, size=n)

    def generate_education_level(self, n: int) -> np.ndarray:
        """Generate education level (0-12 years)."""
        return np.random.randint(0, 13, size=n)

    def generate_practice_indicators(self, n: int) -> Dict[str, np.ndarray]:
        """Generate binary practice adoption indicators."""
        # Correlated adoption logic
        base_prob = 0.3
        return {
            "practice_mixed_farming": np.random.binomial(1, 0.6, n),
            "practice_terracing": np.random.binomial(1, 0.3, n),
            "practice_conservation_tillage": np.random.binomial(1, 0.4, n),
            "practice_agroforestry": np.random.binomial(1, 0.35, n),
        }

    def generate_finance_access(self, n: int) -> np.ndarray:
        """Generate binary finance access indicator."""
        return np.random.binomial(1, 0.45, n)

    def generate_extension_visits(self, n: int) -> np.ndarray:
        """Generate integer frequency of extension visits."""
        return np.random.poisson(lam=3, size=n)

    def generate_hlias(self, n: int) -> np.ndarray:
        """Generate HFIAS score (0-36)."""
        return np.random.randint(0, 37, size=n)

    def generate_csas_and_stability(self, n: int, practices: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Generate CSA_Index and Stability_Score based on practices.
        CSA_Index = sum of binary practice indicators.
        Stability_Score = 1 / CV of simulated NDVI (simulated via practice influence).
        """
        # CSA Index
        csas = (
            practices["practice_mixed_farming"] +
            practices["practice_terracing"] +
            practices["practice_conservation_tillage"] +
            practices["practice_agroforestry"]
        )

        # Simulate Stability Score:
        # Higher CSA adoption -> slightly higher stability (lower CV)
        # Base CV around 0.3, reduced by CSA adoption
        base_cv = 0.4 - (csas.astype(float) * 0.05)
        base_cv = np.clip(base_cv, 0.1, 0.5) # Ensure positive and reasonable
        stability = 1.0 / base_cv
        return {"CSA_Index": csas, "Stability_Score": stability}

    def generate_village_id(self, lat: np.ndarray, lon: np.ndarray, grid_res: float = 0.1) -> List[str]:
        """Derive village_id by rounding coordinates to grid."""
        # Quantize coordinates to grid resolution
        v_lat = np.round(lat / grid_res) * grid_res
        v_lon = np.round(lon / grid_res) * grid_res
        return [f"V{int(la):04d}_{int(lo):04d}" for la, lo in zip(v_lat, v_lon)]

    def generate(self, output_path: Union[str, Path]) -> pd.DataFrame:
        """
        Generate the full synthetic dataset and save to CSV.

        Args:
            output_path: Path to save the CSV file.

        Returns:
            The generated DataFrame.
        """
        self.logger.info(f"Generating synthetic dataset with {NUM_HOUSEHOLDS} households...")

        # Generate base attributes
        household_ids = self.generate_household_id(NUM_HOUSEHOLDS)
        countries = np.random.choice(COUNTRIES, NUM_HOUSEHOLDS)
        coords = self.generate_coordinates(NUM_HOUSEHOLDS, countries[0]) # Simplified: use one country logic or mix
        # Mix countries properly
        lat_list = []
        lon_list = []
        for c in countries:
            c_coords = self.generate_coordinates(1, c)
            lat_list.append(c_coords["latitude"][0])
            lon_list.append(c_coords["longitude"][0])
        lat_arr = np.array(lat_list)
        lon_arr = np.array(lon_list)

        land_sizes = self.generate_land_size(NUM_HOUSEHOLDS)
        education_levels = self.generate_education_level(NUM_HOUSEHOLDS)
        finance_access = self.generate_finance_access(NUM_HOUSEHOLDS)
        practices = self.generate_practice_indicators(NUM_HOUSEHOLDS)
        extension_visits = self.generate_extension_visits(NUM_HOUSEHOLDS)
        hlias = self.generate_hlias(NUM_HOUSEHOLDS)
        csas_scores = self.generate_csas_and_stability(NUM_HOUSEHOLDS, practices)
        village_ids = self.generate_village_id(lat_arr, lon_arr)

        # Construct DataFrame
        df = pd.DataFrame({
            "household_id": household_ids,
            "latitude": lat_arr,
            "longitude": lon_arr,
            "land_size": land_sizes,
            "education_level": education_levels,
            "finance_access": finance_access,
            "practice_mixed_farming": practices["practice_mixed_farming"],
            "practice_terracing": practices["practice_terracing"],
            "practice_conservation_tillage": practices["practice_conservation_tillage"],
            "practice_agroforestry": practices["practice_agroforestry"],
            "extension_visits": extension_visits,
            "hlias": hlias,
            "CSA_Index": csas_scores["CSA_Index"],
            "Stability_Score": csas_scores["Stability_Score"],
            "HFIAS": hlias, # HFIAS is also a column
            "village_id": village_ids
        })

        # Ensure types match schema
        df['household_id'] = df['household_id'].astype(int)
        df['education_level'] = df['education_level'].astype(int)
        df['finance_access'] = df['finance_access'].astype(bool)
        df['practice_mixed_farming'] = df['practice_mixed_farming'].astype(bool)
        df['practice_terracing'] = df['practice_terracing'].astype(bool)
        df['practice_conservation_tillage'] = df['practice_conservation_tillage'].astype(bool)
        df['practice_agroforestry'] = df['practice_agroforestry'].astype(bool)
        df['extension_visits'] = df['extension_visits'].astype(int)
        df['hlias'] = df['hlias'].astype(int)
        df['CSA_Index'] = df['CSA_Index'].astype(float)
        df['Stability_Score'] = df['Stability_Score'].astype(float)
        df['HFIAS'] = df['HFIAS'].astype(float)

        write_csv_strict(df, output_path)
        self.logger.info(f"Synthetic data saved to {output_path}")
        return df


def main():
    """CLI entry point for synthetic generator."""
    parser = argparse.ArgumentParser(description="Generate synthetic data for CI validation.")
    parser.add_argument("--output", type=str, default="data/raw/survey_raw.csv", help="Output CSV path.")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed.")
    args = parser.parse_args()

    logger = setup_logging("synthetic_generator_cli", "INFO")
    generator = SyntheticDataGenerator(seed=args.seed, logger=logger)

    try:
        generator.generate(args.output)
        logger.info("Synthetic generation completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Synthetic generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()