"""
Synthetic Data Generator for CI Validation (Fallback Utility).

This module generates a statistically realistic dataset for CI validation
when real data is missing and the pipeline is running in a CI environment.
It uses Multivariate Normal distributions for continuous variables and
Bernoulli distributions for binary variables, with correlations mimicking
real survey data.
"""

import argparse
import logging
import sys
import os
import random
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd

# Import from project API surface
from src.utils.io_helpers import write_csv_strict, FatalError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
DEFAULT_N_RECORDS = 500
DEFAULT_OUTPUT_PATH = "data/processed/synthetic_analysis_dataset.csv"

class SyntheticDataGenerator:
    """
    Generates synthetic agricultural survey data with realistic correlations.
    """

    def __init__(self, seed: int = RANDOM_SEED):
        self.seed = seed
        self._set_seed()

    def _set_seed(self):
        """Set random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)

    def generate(self, n_records: int = DEFAULT_N_RECORDS) -> pd.DataFrame:
        """
        Generate synthetic dataset.

        Args:
            n_records: Number of records to generate.

        Returns:
            DataFrame with synthetic survey data.
        """
        logger.info(f"Generating {n_records} synthetic records with seed {self.seed}")

        # Generate base continuous variables with correlations
        # Education (years): mean ~10, sd ~3
        # Land Size (hectares): mean ~2.5, sd ~1.5
        # Correlation: Education positively correlates with Land Size
        cov_matrix = np.array([
            [9.0, 1.2],   # Variance of education, Cov(education, land_size)
            [1.2, 2.25]   # Cov(land_size, education), Variance of land_size
        ])

        # Mean vector: [education_mean, land_size_mean]
        mean_vector = [10.0, 2.5]

        try:
            continuous_data = np.random.multivariate_normal(mean_vector, cov_matrix, n_records)
        except np.linalg.LinAlgError as e:
            logger.error(f"Failed to generate multivariate normal data: {e}")
            raise FatalError(f"Failed to generate synthetic data: {e}")

        education = continuous_data[:, 0]
        land_size = continuous_data[:, 1]

        # Ensure positive values
        education = np.maximum(education, 0)
        land_size = np.maximum(land_size, 0)

        # Generate binary variables
        # Finance access: Bernoulli, probability increases with education
        # P(finance) = 0.3 + 0.05 * (education - 5) clipped to [0, 1]
        finance_prob = np.clip(0.3 + 0.05 * (education - 5), 0.0, 1.0)
        finance_access = np.random.binomial(1, finance_prob)

        # Practice variables (Bernoulli)
        # Probability increases with education and land size
        # practice_mixed_farming
        p_mixed = np.clip(0.2 + 0.03 * education + 0.1 * land_size, 0.0, 1.0)
        practice_mixed_farming = np.random.binomial(1, p_mixed)

        # practice_terracing
        p_terracing = np.clip(0.1 + 0.02 * education + 0.05 * land_size, 0.0, 1.0)
        practice_terracing = np.random.binomial(1, p_terracing)

        # practice_conservation_tillage
        p_tillage = np.clip(0.15 + 0.03 * education + 0.08 * land_size, 0.0, 1.0)
        practice_conservation_tillage = np.random.binomial(1, p_tillage)

        # practice_agroforestry
        p_agroforestry = np.clip(0.1 + 0.02 * education + 0.05 * land_size, 0.0, 1.0)
        practice_agroforestry = np.random.binomial(1, p_agroforestry)

        # Generate derived metrics
        # CSA_Index: Sum of binary practice indicators (0-4)
        csa_index = (
            practice_mixed_farming +
            practice_terracing +
            practice_conservation_tillage +
            practice_agroforestry
        )

        # Stability_Score: Simulated based on practice adoption and land size
        # Higher CSA index and larger land size -> higher stability
        # Add noise to make it realistic
        stability_base = 0.5 + 0.1 * csa_index + 0.05 * land_size
        noise = np.random.normal(0, 0.1, n_records)
        stability_score = np.clip(stability_base + noise, 0.0, 1.0)

        # HFIAS (Household Food Insecurity Access Scale): 0-27, lower is better
        # Inverse relationship with education and finance access
        hifias_base = 20 - 1.5 * (education / 10.0) - 5 * finance_access
        hifias_noise = np.random.normal(0, 2, n_records)
        hifias = np.clip(hifias_base + hifias_noise, 0, 27).astype(int)

        # Generate synthetic household IDs and village IDs
        household_ids = [f"HH_{i:05d}" for i in range(1, n_records + 1)]
        village_ids = [f"VIL_{(i % 50) + 1:03d}" for i in range(n_records)]

        # Create DataFrame
        df = pd.DataFrame({
            'household_id': household_ids,
            'village_id': village_ids,
            'education': np.round(education, 1),
            'land_size': np.round(land_size, 2),
            'finance_access': finance_access.astype(int),
            'practice_mixed_farming': practice_mixed_farming.astype(int),
            'practice_terracing': practice_terracing.astype(int),
            'practice_conservation_tillage': practice_conservation_tillage.astype(int),
            'practice_agroforestry': practice_agroforestry.astype(int),
            'CSA_Index': csa_index.astype(int),
            'Stability_Score': np.round(stability_score, 3),
            'HFIAS': hifias
        })

        logger.info(f"Generated dataset with {len(df)} records")
        logger.info(f"CSA_Index range: [{df['CSA_Index'].min()}, {df['CSA_Index'].max()}]")
        logger.info(f"Stability_Score mean: {df['Stability_Score'].mean():.3f}")
        logger.info(f"HFIAS mean: {df['HFIAS'].mean():.1f}")

        return df

    def save(self, df: pd.DataFrame, output_path: str) -> None:
        """
        Save DataFrame to CSV.

        Args:
            df: DataFrame to save.
            output_path: Path to save the CSV file.
        """
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving synthetic dataset to {output_path}")
        write_csv_strict(df, output_path)
        logger.info("Successfully saved synthetic dataset")


def check_real_data_exists(data_dir: str = "data/raw") -> bool:
    """
    Check if real data exists in the specified directory.

    Args:
        data_dir: Path to the data directory.

    Returns:
        True if real data files exist, False otherwise.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.debug(f"Data directory {data_dir} does not exist")
        return False

    # Check for common real data file patterns
    # LSMS-ISA survey data
    survey_files = list(data_path.glob("*survey*.csv")) + list(data_path.glob("*lsms*.csv"))
    # Remote sensing data
    remote_files = list(data_path.glob("*sentinel*.parquet")) + list(data_path.glob("*ndvi*.parquet"))

    real_data_files = survey_files + remote_files

    if real_data_files:
        logger.info(f"Found {len(real_data_files)} potential real data files")
        for f in real_data_files:
            logger.info(f"  - {f.name}")
        return True

    logger.debug("No real data files found in data directory")
    return False


def main():
    """
    Main entry point for the synthetic generator.
    Can be called automatically by the pipeline if real data is missing
    and CI=true environment variable is set.
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic agricultural survey data for CI validation."
    )
    parser.add_argument(
        "--n-records",
        type=int,
        default=DEFAULT_N_RECORDS,
        help=f"Number of records to generate (default: {DEFAULT_N_RECORDS})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output file path (default: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed for reproducibility (default: {RANDOM_SEED})"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for real data existence, do not generate synthetic data"
    )

    args = parser.parse_args()

    # Check if running in CI mode
    is_ci = os.environ.get("CI", "").lower() in ("true", "1", "yes")
    logger.info(f"Running in CI mode: {is_ci}")

    # Check for real data
    real_data_exists = check_real_data_exists("data/raw")

    if args.check_only:
        if real_data_exists:
            logger.info("Real data exists. No synthetic data needed.")
            sys.exit(0)
        else:
            logger.warning("No real data found. Synthetic data would be generated in CI mode.")
            if is_ci:
                logger.info("CI mode detected. Synthetic data generation would proceed.")
            sys.exit(0 if real_data_exists else 1)

    # If real data exists and not in forced synthetic mode, warn but proceed if requested
    if real_data_exists:
        logger.warning("Real data exists. Generating synthetic data may overwrite or duplicate data.")
        if not is_ci:
            logger.info("Not in CI mode. Consider using real data instead.")

    # Generate synthetic data
    generator = SyntheticDataGenerator(seed=args.seed)
    df = generator.generate(n_records=args.n_records)
    generator.save(df, args.output)

    logger.info("Synthetic data generation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
