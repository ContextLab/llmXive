"""
Synthetic Data Generator for CI Validation.

This module generates a statistically realistic dataset for CI validation
when real data is unavailable. It uses Multivariate Normal distributions
for continuous variables and Bernoulli distributions for binary variables.

It enforces a fixed random seed for deterministic generation and respects
the CI environment variable for automatic invocation.
"""
import argparse
import logging
import os
import sys
import random
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
import yaml

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.io_helpers import FatalError, write_csv_strict

# Configuration
RANDOM_SEED = 42
DEFAULT_N_RECORDS = 350  # Slightly above 300 threshold
OUTPUT_PATH = "data/processed/analysis_dataset.csv"
SCHEMA_PATH = "contracts/dataset.schema.yaml"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_schema(schema_path: str) -> dict:
    """Load the dataset schema from YAML."""
    full_path = PROJECT_ROOT / schema_path
    if not full_path.exists():
        raise FatalError(f"Schema file not found: {full_path}")
    with open(full_path, 'r') as f:
        return yaml.safe_load(f)


def generate_synthetic_data(n_records: int, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate a statistically realistic dataset mimicking survey data.
    
    Uses Multivariate Normal for continuous variables (land_size, education)
    and Bernoulli for binary variables (finance_access, practices),
    with correlations mimicking real survey data.
    """
    logger.info(f"Generating {n_records} synthetic records with seed {seed}")
    random.seed(seed)
    np.random.seed(seed)

    # 1. Generate Base Continuous Variables with Correlation
    # Correlation between education and land_size (positive)
    mean = [5.0, 2.0]  # [education_level, land_size]
    cov = [[1.0, 0.3], [0.3, 0.8]]  # Positive correlation 0.3
    
    # Generate from Multivariate Normal
    data = np.random.multivariate_normal(mean, cov, size=n_records)
    education_level = data[:, 0].astype(int)
    # Ensure positive land size
    land_size = np.maximum(data[:, 1], 0.1)

    # 2. Generate Binary Variables (Bernoulli)
    # Probability of finance access depends on education (positive correlation)
    prob_finance = 0.3 + (education_level / 20.0)  # Range ~0.3 to 0.55
    prob_finance = np.clip(prob_finance, 0.1, 0.9)
    finance_access = np.random.binomial(1, prob_finance, size=n_records).astype(bool)

    # Practice adoption probabilities (higher for higher education/finance)
    base_practice_prob = 0.2
    practice_mixed_farming = np.random.binomial(
        1, base_practice_prob + (education_level * 0.02), size=n_records
    ).astype(bool)
    practice_terracing = np.random.binomial(
        1, base_practice_prob + (education_level * 0.015), size=n_records
    ).astype(bool)
    practice_conservation_tillage = np.random.binomial(
        1, base_practice_prob + (education_level * 0.01), size=n_records
    ).astype(bool)
    practice_agroforestry = np.random.binomial(
        1, base_practice_prob + (education_level * 0.015), size=n_records
    ).astype(bool)

    # 3. Generate Derived Variables
    # Extension visits (Poisson distributed, slightly higher for higher education)
    extension_visits = np.random.poisson(
        lam=2.0 + (education_level * 0.2), size=n_records
    ).astype(int)

    # HLIAS (Household Food Insecurity Access Scale) - Integer count
    # Inverse relationship with education/finance
    hlias = np.random.poisson(
        lam=8.0 - (education_level * 0.3) - (finance_access.astype(int) * 2.0),
        size=n_records
    ).astype(int)
    hlias = np.clip(hlias, 0, 24)

    # 4. Calculate Indices
    # CSA_Index: Sum of binary practices (0.0 to 4.0)
    CSA_Index = (
        practice_mixed_farming.astype(int) +
        practice_terracing.astype(int) +
        practice_conservation_tillage.astype(int) +
        practice_agroforestry.astype(int)
    ).astype(float)

    # Stability_Score: Inverse of Coefficient of Variation (simulated)
    # Simulate NDVI CV based on practice adoption (more practices -> more stability)
    # Base CV is 0.4, reduces with CSA index
    simulated_cv = 0.4 - (CSA_Index * 0.05)
    simulated_cv = np.clip(simulated_cv, 0.05, 0.5)
    Stability_Score = 1.0 / simulated_cv

    # HFIAS: Continuous version of HLIAS (simulated)
    HFIAS = hlias.astype(float) * 1.5 + np.random.normal(0, 0.5, size=n_records)
    HFIAS = np.clip(HFIAS, 0, 36)

    # 5. Coordinates (Simulated Malawi/Tanzania region)
    # Center around a point in Malawi
    base_lat = -13.5
    base_lon = 34.0
    # Add noise
    latitude = base_lat + np.random.normal(0, 0.5, size=n_records)
    longitude = base_lon + np.random.normal(0, 0.5, size=n_records)

    # 6. Village ID Derivation
    # Round coordinates to nearest grid cell (buffer_size_km approx 1.0)
    # Using 0.1 degree grid approx 11km, but we'll use a custom grid for uniqueness
    # Round to 1 decimal place for simplicity in this synthetic set
    village_lat = np.round(latitude * 10) / 10
    village_lon = np.round(longitude * 10) / 10
    village_id = [f"V{int(l):03d}_{int(lon):03d}" for l, lon in zip(village_lat, village_lon)]

    # 7. Household IDs
    household_id = np.arange(1, n_records + 1)

    # Construct DataFrame
    df = pd.DataFrame({
        'household_id': household_id,
        'latitude': latitude,
        'longitude': longitude,
        'land_size': land_size,
        'education_level': education_level,
        'finance_access': finance_access,
        'practice_mixed_farming': practice_mixed_farming,
        'practice_terracing': practice_terracing,
        'practice_conservation_tillage': practice_conservation_tillage,
        'practice_agroforestry': practice_agroforestry,
        'extension_visits': extension_visits,
        'hlias': hlias,
        'CSA_Index': CSA_Index,
        'Stability_Score': Stability_Score,
        'HFIAS': HFIAS,
        'village_id': village_id
    })

    return df


def check_real_data_exists(data_path: str) -> bool:
    """Check if real data exists at the specified path."""
    full_path = PROJECT_ROOT / data_path
    return full_path.exists() and full_path.stat().st_size > 0


def main():
    """Main entry point for the synthetic generator."""
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for CI validation")
    parser.add_argument('--n-records', type=int, default=DEFAULT_N_RECORDS, help='Number of records to generate')
    parser.add_argument('--output', type=str, default=OUTPUT_PATH, help='Output file path')
    parser.add_argument('--seed', type=int, default=RANDOM_SEED, help='Random seed')
    args = parser.parse_args()

    # Check for CI environment variable
    is_ci = os.environ.get('CI', '').lower() == 'true'
    
    # Check if real data exists
    real_data_path = args.output
    if check_real_data_exists(real_data_path):
        logger.info(f"Real data already exists at {real_data_path}. Skipping generation.")
        return

    if not is_ci:
        # In non-CI environments, we only generate if explicitly requested or if real data is missing
        # But per spec, this is a fallback utility. We generate if real data is missing.
        logger.warning("Real data missing. Generating synthetic data as fallback.")

    # Generate Data
    try:
        df = generate_synthetic_data(n_records=args.n_records, seed=args.seed)
    except Exception as e:
        raise FatalError(f"Failed to generate synthetic data: {e}")

    # Validate against schema (Basic check)
    schema = load_schema(SCHEMA_PATH)
    required_cols = schema['properties'].keys()
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise FatalError(f"Generated data missing required columns: {missing_cols}")

    # Write Output
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        write_csv_strict(df, str(output_path))
        logger.info(f"Successfully generated synthetic data to {output_path}")
    except Exception as e:
        raise FatalError(f"Failed to write synthetic data: {e}")

    # Verify file was written
    if not output_path.exists():
        raise FatalError("Output file verification failed: file not created.")

    logger.info("Synthetic generation complete.")


if __name__ == "__main__":
    main()