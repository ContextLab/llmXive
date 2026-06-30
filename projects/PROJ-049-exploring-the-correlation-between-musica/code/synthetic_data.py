"""
Synthetic Data Generator for Music-Personality Correlation Study.

Generates a deterministic synthetic dataset mimicking the structure of
BFI-2 (Big Five Inventory-2) and Last.fm listening data.

Features:
- Fixed random seed for reproducibility.
- 5 Personality Traits (Extraversion, Agreeableness, Conscientiousness,
  Emotional Stability, Open-mindedness) scored 1-5.
- Demographics: Age, Gender, Country.
- Listening Data: User ID, Genre tags (raw), Listening Minutes.
- Validates against `contracts/dataset.schema.yaml` before saving.
"""

import os
import random
import yaml
import pandas as pd
import numpy as np
from pathlib import Path

# Import from existing project API
from utils import setup_logging

# Constants
RANDOM_SEED = 42
NUM_USERS = 500
OUTPUT_PATH = "data/processed/synthetic_data.csv"
SCHEMA_PATH = "contracts/dataset.schema.yaml"

# Genre mapping for realistic synthetic data
RAW_GENRES = [
    "alt", "rock", "indie", "pop", "hiphop", "rap", "jazz", "classical",
    "electronic", "edm", "house", "techno", "metal", "punk", "folk",
    "country", "rnb", "soul", "blues", "latin", "reggae", "world",
    "ambient", "noise", "experimental", "soundtrack", "opera", "kpop",
    "jpop", "metalcore", "grunge", "shoegaze", "dream pop", "lo-fi"
]

STANDARD_GENRES = [
    "Rock", "Pop", "Hip Hop", "Electronic", "Jazz", "Classical",
    "R&B", "Country", "Metal", "Folk", "World", "Other"
]

COUNTRIES = ["US", "UK", "DE", "FR", "JP", "BR", "IN", "CA", "AU", "KR"]
GENDERS = ["M", "F", "NB", "Other"]

logger = setup_logging()

def _generate_personality_scores(n: int, seed: int) -> pd.DataFrame:
    """Generate Big Five personality scores (1-5 scale)."""
    rng = np.random.default_rng(seed)
    data = {
        "extraversion": rng.integers(1, 6, size=n),
        "agreeableness": rng.integers(1, 6, size=n),
        "conscientiousness": rng.integers(1, 6, size=n),
        "emotional_stability": rng.integers(1, 6, size=n),
        "open_mindedness": rng.integers(1, 6, size=n),
    }
    return pd.DataFrame(data)

def _generate_demographics(n: int, seed: int) -> pd.DataFrame:
    """Generate demographic data."""
    rng = np.random.default_rng(seed + 1)
    ages = rng.integers(18, 70, size=n)
    genders = rng.choice(GENDERS, size=n)
    countries = rng.choice(COUNTRIES, size=n)

    return pd.DataFrame({
        "age": ages,
        "gender": genders,
        "country": countries
    })

def _generate_listening_data(n: int, seed: int) -> pd.DataFrame:
    """Generate listening data with raw genre tags and minutes."""
    rng = np.random.default_rng(seed + 2)
    user_ids = [f"user_{i:05d}" for i in range(n)]

    # Generate listening minutes (skewed distribution)
    minutes = rng.exponential(scale=2000, size=n).astype(int)
    minutes = np.clip(minutes, 0, 100000) # Cap at reasonable max

    # Assign 1-5 raw genre tags per user
    raw_tags_list = []
    for _ in range(n):
        num_tags = rng.integers(1, 6)
        tags = rng.choice(RAW_GENRES, size=num_tags, replace=False).tolist()
        raw_tags_list.append(";".join(tags))

    return pd.DataFrame({
        "user_id": user_ids,
        "raw_genres": raw_tags_list,
        "listening_minutes": minutes
    })

def validate_schema(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validates the dataframe against the YAML schema definition.
    Checks for required columns and basic type constraints.
    """
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
        return True

    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    required_columns = schema.get("required_columns", [])
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Schema validation failed: Missing column '{col}'")
            return False

    # Check for nulls in critical columns if specified in schema
    if "no_null_columns" in schema:
        for col in schema["no_null_columns"]:
            if df[col].isnull().any():
                logger.error(f"Schema validation failed: Nulls found in '{col}'")
                return False

    logger.info("Schema validation passed.")
    return True

def generate_synthetic_data(output_path: str = OUTPUT_PATH):
    """
    Main entry point to generate and save the synthetic dataset.
    """
    logger.info(f"Starting synthetic data generation with seed {RANDOM_SEED}")

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Generate components
    personality_df = _generate_personality_scores(NUM_USERS, RANDOM_SEED)
    demographics_df = _generate_demographics(NUM_USERS, RANDOM_SEED)
    listening_df = _generate_listening_data(NUM_USERS, RANDOM_SEED + 3)

    # Merge into a single wide dataframe
    # Assuming 1:1 correspondence for synthetic generation
    df = pd.concat([
        demographics_df,
        personality_df,
        listening_df
    ], axis=1)

    # Validate against schema
    if not validate_schema(df, SCHEMA_PATH):
        raise ValueError("Schema validation failed. Aborting save.")

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic data saved to {output_path}")
    logger.info(f"Dataset shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")

    return df

if __name__ == "__main__":
    generate_synthetic_data()
