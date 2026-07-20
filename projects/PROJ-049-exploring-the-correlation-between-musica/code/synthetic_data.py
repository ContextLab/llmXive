"""
Synthetic Data Generator.

Generates a deterministic synthetic dataset for validation purposes,
strictly adhering to the schema defined in contracts/dataset.schema.yaml.

This generator is used in "Validation Mode" when no real data source is
available or when explicitly requested via --force-synthetic.
"""

import os
import random
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

from utils import setup_logging

logger = setup_logging(__name__)
CONTRACTS_DIR = Path("contracts")
SCHEMA_FILE = CONTRACTS_DIR / "dataset.schema.yaml"

def generate_synthetic_data(n_rows: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Generate deterministic synthetic data matching the project schema.
    
    The schema requires: user_id, openness, conscientiousness, extraversion,
    agreeableness, neuroticism, age, gender, country.
    
    Args:
        n_rows: Number of rows to generate (default 1000).
        seed: Random seed for reproducibility.
        
    Returns:
        DataFrame with schema-compliant columns.
    """
    # Set seeds for full reproducibility
    random.seed(seed)
    np.random.seed(seed)
    
    # 1. User IDs
    user_ids = [f"user_{i:05d}" for i in range(n_rows)]
    
    # 2. Personality Traits (Big Five)
    # Simulating realistic distributions (normal approx, clipped 0-100)
    openness = np.clip(np.random.normal(52, 13, n_rows), 0, 100).astype(int)
    conscientiousness = np.clip(np.random.normal(60, 10, n_rows), 0, 100).astype(int)
    extraversion = np.clip(np.random.normal(50, 15, n_rows), 0, 100).astype(int)
    agreeableness = np.clip(np.random.normal(55, 12, n_rows), 0, 100).astype(int)
    neuroticism = np.clip(np.random.normal(45, 14, n_rows), 0, 100).astype(int)
    
    # 3. Demographics
    # Age: 18-65 (uniform distribution as requested)
    age = np.random.randint(18, 66, n_rows)
    
    # Gender: Categorical
    gender_options = ["Male", "Female", "Non-binary"]
    gender_probs = [0.48, 0.48, 0.04]
    gender = np.random.choice(gender_options, n_rows, p=gender_probs)
    
    # Country: Categorical
    country_options = ["US", "UK", "DE", "FR", "JP"]
    country_probs = [0.40, 0.20, 0.15, 0.15, 0.10]
    country = np.random.choice(country_options, n_rows, p=country_probs)
    
    # Construct DataFrame
    df = pd.DataFrame({
        "user_id": user_ids,
        "openness": openness,
        "conscientiousness": conscientiousness,
        "extraversion": extraversion,
        "agreeableness": agreeableness,
        "neuroticism": neuroticism,
        "age": age,
        "gender": gender,
        "country": country
    })
    
    logger.info(f"Generated {n_rows} synthetic rows with schema-compliant columns.")
    return df

def validate_schema(df: pd.DataFrame, schema_path: Optional[Path] = None) -> bool:
    """
    Validate DataFrame against the project's dataset schema.
    
    Args:
        df: DataFrame to validate.
        schema_path: Path to schema file (defaults to contracts/dataset.schema.yaml).
        
    Returns:
        True if valid, raises error or returns False if invalid.
    """
    if schema_path is None:
        schema_path = SCHEMA_FILE
        
    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}, skipping strict validation.")
        return True
        
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        required_fields = schema.get('fields', [])
        df_columns = set(df.columns)
        
        missing_fields = set(required_fields) - df_columns
        if missing_fields:
            logger.error(f"Schema validation failed: Missing fields {missing_fields}")
            return False
            
        logger.info("Schema validation passed.")
        return True
    except Exception as e:
        logger.error(f"Error reading schema: {e}")
        return False

def main():
    """Generate and save synthetic data to the required path."""
    # Ensure output directory exists
    output_path = Path("data/processed/synthetic_data.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    df = generate_synthetic_data(n_rows=1000, seed=42)
    
    # Validate against schema before saving
    if not validate_schema(df):
        logger.error("Schema validation failed. Aborting save.")
        raise ValueError("Synthetic data does not match schema.")
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic data successfully saved to {output_path}")

if __name__ == "__main__":
    main()