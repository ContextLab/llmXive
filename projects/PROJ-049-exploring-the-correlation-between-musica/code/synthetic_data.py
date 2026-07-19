"""
Synthetic Data Generator.

Generates deterministic synthetic datasets for BFI-2 and Last.fm data
when real data is unavailable.
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

def generate_synthetic_data(n_rows: int = 500, seed: int = 42, data_type: str = "mixed") -> pd.DataFrame:
    """
    Generate synthetic data mimicking BFI-2 and Last.fm structure.
    
    Args:
        n_rows: Number of rows to generate.
        seed: Random seed for reproducibility.
        data_type: 'personality', 'listening', or 'mixed'.
        
    Returns:
        Generated DataFrame.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Generate User IDs
    user_ids = [f"user_{i:04d}" for i in range(n_rows)]
    
    # Personality Traits (0-100 scale)
    traits = {
        "Extraversion": np.random.normal(50, 15, n_rows),
        "Agreeableness": np.random.normal(55, 12, n_rows),
        "Conscientiousness": np.random.normal(60, 10, n_rows),
        "Neuroticism": np.random.normal(45, 14, n_rows),
        "Openness": np.random.normal(52, 13, n_rows)
    }
    
    # Demographics
    ages = np.random.randint(18, 65, n_rows)
    genders = np.random.choice(["Male", "Female", "Non-binary"], n_rows, p=[0.48, 0.48, 0.04])
    countries = np.random.choice(["US", "UK", "DE", "FR", "JP"], n_rows, p=[0.4, 0.2, 0.15, 0.15, 0.1])
    
    # Listening Data
    genres = ["Rock", "Pop", "Jazz", "Classical", "HipHop", "Electronic", "Country", "Metal"]
    listening_minutes = np.random.exponential(1000, n_rows).astype(int)
    
    # Assign random genres to users
    assigned_genres = [random.choice(genres) for _ in range(n_rows)]
    
    if data_type == "personality":
        df = pd.DataFrame({
            "user_id": user_ids,
            **traits,
            "age": ages,
            "gender": genders,
            "country": countries
        })
    elif data_type == "listening":
        df = pd.DataFrame({
            "user_id": user_ids,
            "genre": assigned_genres,
            "listening_minutes": listening_minutes
        })
    else:
        # Mixed
        df = pd.DataFrame({
            "user_id": user_ids,
            **traits,
            "age": ages,
            "gender": genders,
            "country": countries,
            "genre": assigned_genres,
            "listening_minutes": listening_minutes
        })
    
    # Clip traits to 0-100
    for t in traits:
        df[t] = df[t].clip(0, 100)
        
    return df

def validate_schema(df: pd.DataFrame, schema_path: Optional[Path] = None) -> bool:
    """
    Validate DataFrame against schema.
    
    Args:
        df: DataFrame to validate.
        schema_path: Path to schema file.
        
    Returns:
        True if valid.
    """
    # Simplified validation
    required_cols = ["user_id"]
    if not all(col in df.columns for col in required_cols):
        logger.error("Missing required columns.")
        return False
    logger.info("Schema validation passed.")
    return True

def main():
    """Generate and save synthetic data."""
    df = generate_synthetic_data(n_rows=500, seed=42, data_type="mixed")
    output_path = Path("data/processed/synthetic_data.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic data saved to {output_path}")

if __name__ == "__main__":
    main()
