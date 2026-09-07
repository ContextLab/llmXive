"""
Structural Validation Generator for PROJ-006.

Generates a dataset for Structural Validation Mode when real data is unavailable.
Uses Multivariate Normal distributions for continuous variables and Bernoulli for binary variables.
Generates raw fields AND derived metrics (CSA_Index, Stability_Score) to ensure the pipeline is executable.
Strictly decoupled from analysis logic (fixed seed, independent RNG).
"""

import argparse
import logging
import sys
import os
import random
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd

# Import local helpers using the exact API surface provided
# The API surface lists: setup_logging, FatalError, IntegrityError, etc.
# We assume the logger name is the module name or a generic 'structural_validation'
# The error in the logs was "Invalid log level: synthetic_generator", implying the function
# expects a valid log level string (e.g., 'INFO'), not a module name.
# We will implement a robust logging setup or import the fixed helper.

# Since we cannot edit io_helpers.py in this task (it's not T010), we must handle logging
# safely here or assume the fix in T010a will handle the import.
# However, to ensure this script runs standalone, we will implement a local logging setup
# that mimics the expected behavior, or import if available.
# Given the constraint "Extend, don't re-author", and the fact that io_helpers.py exists,
# we will try to import. If it fails due to the specific bug mentioned in the execution log,
# we will catch it and use a fallback to ensure the script runs (as the bug is in the helper, not this logic).
# BUT, the instruction says "If a name does not exist there, either add it to the appropriate file...".
# We are allowed to add artifacts. We should probably fix the import or provide a safe wrapper.
# Let's try to import and if the specific error occurs, we'll handle it gracefully or assume the
# user has fixed io_helpers.py (since T009 is marked done, but the log shows a crash).
# Actually, the log shows T009 is done but the code crashes. This implies the code in io_helpers.py
# is buggy. Since I cannot edit io_helpers.py in T010 (it's a different task), I must ensure
# this script doesn't crash on import if the bug exists.
# Strategy: Try to import. If it fails, use a simple fallback logger.

def _get_logger(name: str) -> logging.Logger:
    """Safely get a logger, falling back to standard setup if the project helper fails."""
    try:
        from src.utils.io_helpers import setup_logging
        # The error was "Invalid log level: synthetic_generator".
        # This implies setup_logging takes (name) and tries to parse it as a level?
        # Or maybe it takes (name, level) and the caller passed the wrong args?
        # The log says: logger = setup_logging("synthetic_generator") -> ValueError: Invalid log level: synthetic_generator
        # This implies setup_logging expects a log level string, not a name?
        # Or it expects a name and internally fails?
        # To be safe, we will use standard logging.
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    except Exception:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = _get_logger("structural_validation_generator")

# Constants for generation
SEED = 42
NUM_RECORDS = 500  # Ensure > 300 for validation
CONTINUOUS_MEAN = 0.0
CONTINUOUS_STD = 0.5
BINARY_PROB = 0.5

class StructuralValidationGenerator:
    """Generates structural validation data for the agriculture optimization pipeline."""

    def __init__(self, seed: int = SEED):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        random.seed(seed)
        logger.info(f"Initialized StructuralValidationGenerator with seed {seed}")

    def _generate_continuous(self, shape: tuple, mean: float = CONTINUOUS_MEAN, scale: float = CONTINUOUS_STD) -> np.ndarray:
        """Generate multivariate normal data."""
        return self.rng.normal(loc=mean, scale=scale, size=shape)

    def _generate_binary(self, shape: tuple, prob: float = BINARY_PROB) -> np.ndarray:
        """Generate Bernoulli data."""
        return self.rng.random(shape) < prob

    def generate(self, num_records: int = NUM_RECORDS) -> pd.DataFrame:
        """
        Generate the full dataset with raw fields and derived metrics.
        
        Columns:
        - household_id (int)
        - latitude, longitude (float)
        - land_size (float)
        - education_level (int)
        - finance_access (bool)
        - practice_mixed_farming, practice_terracing, practice_conservation_tillage, practice_agroforestry (bool)
        - extension_visits (int)
        - hlias (int)
        - CSA_Index (float) - Derived
        - Stability_Score (float) - Derived
        - village_id (str) - Derived
        """
        logger.info(f"Generating {num_records} records...")

        # 1. Raw Fields
        household_ids = list(range(1, num_records + 1))
        
        # Coordinates (simulating a region)
        lats = self._generate_continuous((num_records,), mean=0.0, scale=0.1) + 10.0 # Base lat
        lons = self._generate_continuous((num_records,), mean=0.0, scale=0.1) + 30.0 # Base lon
        
        land_size = np.abs(self._generate_continuous((num_records,), mean=2.0, scale=1.0)) # Positive land size
        education_level = self.rng.integers(low=1, high=13, size=num_records) # 1-12
        
        finance_access = self._generate_binary((num_records,)).astype(int)
        
        # Practices
        practice_mixed_farming = self._generate_binary((num_records,)).astype(int)
        practice_terracing = self._generate_binary((num_records,)).astype(int)
        practice_conservation_tillage = self._generate_binary((num_records,)).astype(int)
        practice_agroforestry = self._generate_binary((num_records,)).astype(int)
        
        extension_visits = self.rng.integers(low=0, high=10, size=num_records)
        hlias = self.rng.integers(low=0, high=28, size=num_records) # HFIAS score 0-28

        # 2. Derived Metrics
        # CSA_Index: Sum of binary practice indicators (0 to 4)
        # Map practice_* to CSA_Index
        csa_index = (
            practice_mixed_farming + 
            practice_terracing + 
            practice_conservation_tillage + 
            practice_agroforestry
        )

        # Stability_Score: Derived from synthetic NDVI proxy.
        # Since we don't have real NDVI, we simulate a stability score based on land size and practices.
        # Higher practices -> higher stability.
        # Normalized 0-100.
        stability_base = 50.0
        stability_bonus = (csa_index * 10.0) + (extension_visits * 2.0)
        stability_noise = self._generate_continuous((num_records,), mean=0, scale=5.0)
        stability_score = stability_base + stability_bonus + stability_noise
        stability_score = np.clip(stability_score, 0, 100)

        # Village ID: Derived from coordinates (grid resolution 0.1)
        # Formula: village_id = f'{int(lat / grid_resolution) * grid_resolution}_{int(lon / grid_resolution) * grid_resolution}'
        grid_res = 0.1
        village_ids = [
            f"{int(lat / grid_res) * grid_res}_{int(lon / grid_res) * grid_res}" 
            for lat, lon in zip(lats, lons)
        ]

        # Construct DataFrame
        data = {
            'household_id': household_ids,
            'latitude': lats,
            'longitude': lons,
            'land_size': land_size,
            'education_level': education_level,
            'finance_access': finance_access,
            'practice_mixed_farming': practice_mixed_farming,
            'practice_terracing': practice_terracing,
            'practice_conservation_tillage': practice_conservation_tillage,
            'practice_agroforestry': practice_agroforestry,
            'extension_visits': extension_visits,
            'hlias': hlias,
            'CSA_Index': csa_index,
            'Stability_Score': stability_score,
            'village_id': village_ids
        }

        df = pd.DataFrame(data)
        logger.info(f"Generated DataFrame with shape {df.shape}")
        return df

    def save(self, df: pd.DataFrame, output_path: str) -> None:
        """Save the dataset to CSV."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        logger.info(f"Saved dataset to {output_path}")

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate structural validation data.")
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/raw/structural_validation_data.csv",
        help="Output file path."
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=SEED, 
        help="Random seed."
    )
    parser.add_argument(
        "--num-records", 
        type=int, 
        default=NUM_RECORDS, 
        help="Number of records to generate."
    )

    args = parser.parse_args()

    try:
        generator = StructuralValidationGenerator(seed=args.seed)
        df = generator.generate(num_records=args.num_records)
        generator.save(df, args.output)
        logger.info("Structural validation generation completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
