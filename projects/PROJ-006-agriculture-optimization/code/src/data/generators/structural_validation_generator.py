"""
Structural Validation Data Generator

Generates a synthetic dataset for Structural Validation Mode when real data is unavailable.
Uses Multivariate Normal distributions for continuous variables and Bernoulli for binary variables.
Generates both raw fields and derived metrics (CSA_Index, Stability_Score) to ensure pipeline executability.
Strictly decoupled from analysis logic (fixed seed, independent RNG).
"""
import argparse
import logging
import sys
import os
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

# Import logging helper from project utils
# Note: The error log indicated 'Invalid log level: synthetic_generator' when passing module name directly.
# We will pass a valid log level string (e.g., 'INFO') or handle the setup correctly.
# Based on the error: setup_logging("synthetic_generator") raised ValueError.
# We assume setup_logging expects a valid log level string like "INFO", "DEBUG", etc., or we must fix io_helpers.
# However, per constraints, we must extend existing files if needed.
# The error came from io_helpers.py:25: `raise ValueError(f"Invalid log level: {level}")`.
# This implies `setup_logging` expects a level string, not a name.
# We will import and use it correctly here: setup_logging("INFO").
from src.utils.io_helpers import setup_logging, write_csv_strict, FatalError

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "structural_validation_data.csv"
DEFAULT_N_HOUSEHOLDS = 500
RANDOM_SEED = 42

# Initialize logger
# Passing "INFO" to avoid the ValueError seen in execution logs
logger = setup_logging("INFO")


class StructuralValidationGenerator:
    """
    Generates structural validation data with specific statistical properties.
    """

    def __init__(self, n_households: int = DEFAULT_N_HOUSEHOLDS, seed: int = RANDOM_SEED):
        self.n_households = n_households
        self.seed = seed
        self._rng = np.random.default_rng(seed)
        random.seed(seed)
        logger.info(f"Initialized StructuralValidationGenerator with N={n_households}, Seed={seed}")

    def _generate_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate random latitude/longitude around a central point (e.g., Malawi region)."""
        # Center around Malawi (approx -13.5, 34.5)
        lat_center = -13.5
        lon_center = 34.5
        # Spread ~1 degree for diversity
        lats = self._rng.normal(loc=lat_center, scale=0.5, size=self.n_households)
        lons = self._rng.normal(loc=lon_center, scale=0.5, size=self.n_households)
        return lats, lons

    def _generate_continuous_vars(self) -> Dict[str, np.ndarray]:
        """
        Generate continuous variables using Multivariate Normal.
        Mean=0, Cov=I scaled by 0.5 as per requirements.
        Then shift/scale to realistic ranges.
        """
        # Define correlation structure (identity scaled by 0.5)
        mean = np.zeros(4) # land_size, education_level, extension_visits, hlias
        cov = np.eye(4) * 0.5

        raw_data = self._rng.multivariate_normal(mean, cov, size=self.n_households)

        # Map to realistic ranges
        # land_size: 0.5 to 10 hectares
        land_size = 0.5 + (raw_data[:, 0] * 2 + 4) # Center ~4, scale ~2
        land_size = np.clip(land_size, 0.5, 10.0)

        # education_level: 0 to 12 years (integer)
        education_level = np.round(raw_data[:, 1] * 3 + 6).astype(int)
        education_level = np.clip(education_level, 0, 12)

        # extension_visits: 0 to 20 (integer)
        extension_visits = np.round(raw_data[:, 2] * 4 + 8).astype(int)
        extension_visits = np.clip(extension_visits, 0, 20)

        # hlias: 0 to 50 (Food insecurity score)
        hlias = np.round(raw_data[:, 3] * 10 + 25).astype(int)
        hlias = np.clip(hlias, 0, 50)

        return {
            "land_size": land_size,
            "education_level": education_level,
            "extension_visits": extension_visits,
            "hlias": hlias
        }

    def _generate_binary_vars(self) -> Dict[str, np.ndarray]:
        """Generate binary practice indicators using Bernoulli distribution."""
        # Probabilities for practices (approx 30-50% adoption)
        p_mixed = 0.4
        p_terracing = 0.3
        p_tillage = 0.35
        p_agroforestry = 0.25

        return {
            "practice_mixed_farming": self._rng.binomial(1, p_mixed, self.n_households).astype(bool),
            "practice_terracing": self._rng.binomial(1, p_terracing, self.n_households).astype(bool),
            "practice_conservation_tillage": self._rng.binomial(1, p_tillage, self.n_households).astype(bool),
            "practice_agroforestry": self._rng.binomial(1, p_agroforestry, self.n_households).astype(bool),
            "finance_access": self._rng.binomial(1, 0.6, self.n_households).astype(bool) # 60% access
        }

    def _generate_derived_metrics(self, practices: Dict[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate derived metrics:
        CSA_Index: Sum of binary practice indicators.
        Stability_Score: Derived from a synthetic NDVI time-series simulation.
        """
        # CSA Index: Sum of practices (0 to 4)
        csa_index = (
            practices["practice_mixed_farming"].astype(int) +
            practices["practice_terracing"].astype(int) +
            practices["practice_conservation_tillage"].astype(int) +
            practices["practice_agroforestry"].astype(int)
        ).astype(float)

        # Stability Score: Simulate from NDVI variance
        # We generate a synthetic NDVI time series for each household (e.g., 12 months)
        # Then calculate CV (Coefficient of Variation) and set Stability = 1 / (CV + epsilon)
        n_months = 12
        ndvi_mean = 0.5
        ndvi_std = 0.1

        # Generate NDVI time series: shape (n_households, n_months)
        ndvi_series = self._rng.normal(loc=ndvi_mean, scale=ndvi_std, size=(self.n_households, n_months))
        ndvi_series = np.clip(ndvi_series, 0, 1) # NDVI range [0, 1]

        # Calculate mean and std per household
        ndvi_mean_per_household = np.mean(ndvi_series, axis=1)
        ndvi_std_per_household = np.std(ndvi_series, axis=1)

        # Avoid division by zero
        epsilon = 1e-6
        cv = ndvi_std_per_household / (ndvi_mean_per_household + epsilon)
        stability_score = 1.0 / (cv + epsilon)

        # Normalize stability score to a reasonable range (e.g., 0-100)
        # Just scaling for visualization, keeping relative order
        stability_score = (stability_score - stability_score.min()) / (stability_score.max() - stability_score.min() + epsilon) * 100.0

        return csa_index, stability_score

    def generate(self) -> pd.DataFrame:
        """Generate the full dataset."""
        logger.info("Generating coordinates...")
        lats, lons = self._generate_coordinates()

        logger.info("Generating continuous variables...")
        cont_vars = self._generate_continuous_vars()

        logger.info("Generating binary variables...")
        bin_vars = self._generate_binary_vars()

        logger.info("Calculating derived metrics (CSA_Index, Stability_Score)...")
        csa_index, stability_score = self._generate_derived_metrics(bin_vars)

        # Construct DataFrame
        data = {
            "household_id": np.arange(1, self.n_households + 1),
            "latitude": lats,
            "longitude": lons,
            "land_size": cont_vars["land_size"],
            "education_level": cont_vars["education_level"],
            "finance_access": bin_vars["finance_access"],
            "practice_mixed_farming": bin_vars["practice_mixed_farming"],
            "practice_terracing": bin_vars["practice_terracing"],
            "practice_conservation_tillage": bin_vars["practice_conservation_tillage"],
            "practice_agroforestry": bin_vars["practice_agroforestry"],
            "extension_visits": cont_vars["extension_visits"],
            "hlias": cont_vars["hlias"], # Note: task spec says 'hlias' in schema, 'HFIAS' in description. Using 'hlias' as per schema T007.
            "CSA_Index": csa_index,
            "Stability_Score": stability_score,
            "village_id": [f"{int(lat/0.1)*0.1}_{int(lon/0.1)*0.1}" for lat, lon in zip(lats, lons)]
        }

        df = pd.DataFrame(data)

        # Ensure HFIAS column exists if schema expects 'HFIAS' (Task T007 says 'hlias', description says 'HFIAS')
        # T007 explicitly lists 'hlias' (int). We keep 'hlias'.
        # If T018b expects 'HFIAS', we might need an alias, but T007 is the contract.
        # We will add 'HFIAS' as an alias to be safe for downstream tasks if they expect it,
        # but primary is 'hlias' as per T007.
        df["HFIAS"] = df["hlias"].astype(float)

        return df

    def save(self, df: pd.DataFrame, path: Path) -> None:
        """Save DataFrame to CSV."""
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving dataset to {path}")
        write_csv_strict(df, str(path))
        logger.info("Save complete.")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate structural validation dataset.")
    parser.add_argument("--n-households", type=int, default=DEFAULT_N_HOUSEHOLDS, help="Number of households to generate.")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed.")
    parser.add_argument("--output", type=str, default=str(OUTPUT_PATH), help="Output file path.")
    args = parser.parse_args()

    try:
        generator = StructuralValidationGenerator(n_households=args.n_households, seed=args.seed)
        df = generator.generate()
        generator.save(df, Path(args.output))
        logger.info("Structural validation generation successful.")
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise FatalError(f"Structural validation generation failed: {e}")


if __name__ == "__main__":
    main()
