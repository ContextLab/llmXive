"""
Synthetic data generator for CI validation ONLY.

This module provides a mechanism to generate synthetic analysis datasets
strictly for Continuous Integration (CI) environments where real data
ingestion is not feasible or desired.

CRITICAL: This generator MUST raise a FatalError if:
1. The '--synthetic' flag is NOT set (production mode).
2. Real data is missing and no fallback is permitted.

This prevents silent fallback to mock data in production pipelines,
ensuring data integrity and research validity.
"""

import argparse
import logging
import sys
import os
import random
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from project API surface
from src.utils.io_helpers import FatalError, write_csv_strict
from src.config.constants import PROJECT_ROOT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for synthetic generation
SYNTHETIC_SEED = 42
NUM_SYNTHETIC_RECORDS = 100  # Small dataset for CI validation
COUNTRIES = ["Malawi", "Tanzania"]
HOUSEHOLD_PREFIX = "HH_"

class SyntheticDataGenerator:
    """Generates synthetic analysis datasets for CI validation."""

    def __init__(self, seed: int = SYNTHETIC_SEED):
        """
        Initialize the generator with a random seed.

        Args:
            seed: Random seed for reproducibility.
        """
        self.seed = seed
        random.seed(seed)
        logger.info(f"SyntheticDataGenerator initialized with seed {seed}")

    def _generate_household_id(self, index: int) -> str:
        """Generate a unique household ID."""
        country = random.choice(COUNTRIES)
        return f"{HOUSEHOLD_PREFIX}{country}_{index:05d}"

    def _generate_csa_index(self) -> float:
        """
        Generate a synthetic CSA Index.

        The CSA Index is a composite score based on adoption of climate-smart
        practices. Range: 0.0 to 1.0.
        """
        # Simulate a distribution skewed towards lower adoption with some high adopters
        return min(1.0, max(0.0, random.gauss(0.4, 0.2)))

    def _generate_stability_score(self, csa_index: float) -> float:
        """
        Generate a synthetic Yield Stability Score.

        Intentionally correlated with CSA Index to simulate the research hypothesis,
        but with noise to represent real-world variability.
        """
        # Base correlation: higher CSA -> higher stability
        base_stability = 0.3 + (0.5 * csa_index)
        noise = random.gauss(0, 0.1)
        return min(1.0, max(0.0, base_stability + noise))

    def _generate_hfias(self) -> int:
        """
        Generate a synthetic Household Food Insecurity Access Scale (HFIAS).

        Range: 0 (Food Secure) to 27 (Severely Food Insecure).
        """
        # Simulate a distribution where most are moderately secure
        return max(0, min(27, int(random.gauss(10, 5))))

    def _generate_financial_access(self) -> bool:
        """Generate a synthetic Financial Access flag."""
        return random.random() < 0.4  # 40% have access

    def generate_record(self, index: int) -> Dict[str, Any]:
        """
        Generate a single synthetic record matching the analysis dataset schema.

        Args:
            index: Record index for ID generation.

        Returns:
            Dictionary containing all required fields.
        """
        csa_index = self._generate_csa_index()
        stability_score = self._generate_stability_score(csa_index)

        return {
            "household_id": self._generate_household_id(index),
            "country": random.choice(COUNTRIES),
            "survey_year": random.choice([2019, 2020, 2021]),
            "csa_index": round(csa_index, 4),
            "stability_score": round(stability_score, 4),
            "hfias": self._generate_hfias(),
            "financial_access": self._generate_financial_access(),
            "latitude": round(random.uniform(-15.0, -9.0), 4),  # Approx Africa lat
            "longitude": round(random.uniform(28.0, 40.0), 4),  # Approx Africa long
            "plot_area_ha": round(random.gauss(1.5, 0.5), 2),
            "yield_ton_ha": round(random.gauss(2.0, 0.8), 2)
        }

    def generate_dataset(self, num_records: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate a full synthetic dataset.

        Args:
            num_records: Number of records to generate. Defaults to NUM_SYNTHETIC_RECORDS.

        Returns:
            List of dictionaries, each representing a synthetic household record.
        """
        n = num_records or NUM_SYNTHETIC_RECORDS
        logger.info(f"Generating {n} synthetic records...")
        return [self.generate_record(i) for i in range(n)]

def check_real_data_exists(output_path: Path) -> bool:
    """
    Check if the expected real data file exists.

    Args:
        output_path: Path to the expected real data file.

    Returns:
        True if the file exists, False otherwise.
    """
    # Check for the primary analysis dataset
    if output_path.exists():
        logger.info(f"Real data found at {output_path}")
        return True

    # Also check for common alternative locations
    alt_paths = [
        PROJECT_ROOT / "data" / "processed" / "analysis_dataset.csv",
        PROJECT_ROOT / "data" / "raw" / "lsms_isa_processed.csv"
    ]

    for alt in alt_paths:
        if alt.exists():
            logger.info(f"Real data found at alternate path {alt}")
            return True

    logger.warning("No real data found in expected locations.")
    return False

def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the synthetic data generator.

    This function enforces the 'fail loudly' constraint:
    - If --synthetic is NOT provided AND real data is missing, raise FatalError.
    - If --synthetic IS provided, generate synthetic data for CI.

    Args:
        args: Command line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for CI validation ONLY.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        WARNING: This script is for CI/CD testing only.
        In production, real data must be present. If real data is missing
        and --synthetic is not set, this script will fail.
        """
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Force generation of synthetic data (CI mode only)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "data" / "processed" / "synthetic_analysis_dataset.csv"),
        help="Output path for the generated CSV file."
    )
    parser.add_argument(
        "--n-records",
        type=int,
        default=NUM_SYNTHETIC_RECORDS,
        help="Number of synthetic records to generate."
    )

    parsed_args = parser.parse_args(args)

    output_path = Path(parsed_args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # CRITICAL CHECK: Production Mode Enforcement
    if not parsed_args.synthetic:
        if not check_real_data_exists(output_path):
            error_msg = (
                "CRITICAL: Real data is missing and --synthetic flag was not set. "
                "This script is for CI validation only. "
                "To proceed with synthetic data (CI only), add --synthetic. "
                "To proceed with real data, ensure the pipeline has downloaded it first."
            )
            logger.error(error_msg)
            raise FatalError(error_msg)
        else:
            logger.info("Real data detected. Skipping synthetic generation.")
            return 0

    # Synthetic Mode (CI Only)
    logger.warning("Running in SYNTHETIC mode (--synthetic flag set).")
    logger.warning("This data is NOT suitable for production analysis.")

    try:
        generator = SyntheticDataGenerator()
        dataset = generator.generate_dataset(num_records=parsed_args.n_records)

        if not dataset:
            raise FatalError("Failed to generate any synthetic records.")

        # Write to CSV
        write_csv_strict(dataset, output_path)

        logger.info(f"Successfully generated {len(dataset)} synthetic records to {output_path}")
        return 0

    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        raise FatalError(f"Synthetic data generation failed: {e}")

if __name__ == "__main__":
    sys.exit(main())
