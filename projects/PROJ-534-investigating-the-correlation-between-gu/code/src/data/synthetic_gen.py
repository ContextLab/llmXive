import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any
import logging
from code.src.utils.config import (
    get_raw_data_dir,
    get_project_root,
    ensure_directories,
    set_global_seed,
    SEED
)

def generate_participant_demographics(n_participants: int, seed: int = 42) -> pd.DataFrame:
    """Generates participant demographics."""
    np.random.seed(seed)
    age = np.random.randint(65, 90, size=n_participants)
    sex = np.random.choice(['Male', 'Female'], size=n_participants)
    bmi = np.random.uniform(20, 35, size=n_participants)
    df = pd.DataFrame({'participant_id': range(n_participants), 'age': age, 'sex': sex, 'bmi': bmi})
    return df

def generate_lifestyle_factors(n_participants: int, seed: int = 42) -> pd.DataFrame:
    """Generates lifestyle factors."""
    np.random.seed(seed)
    dietary_fiber = np.random.uniform(10, 40, size=n_participants)
    antibiotic_use = np.random.choice([True, False], size=n_participants, p=[0.2, 0.8])
    df = pd.DataFrame({'dietary_fiber': dietary_fiber, 'antibiotic_use': antibiotic_use})
    return df

def generate_microbiome_data(n_participants: int, seed: int = 42) -> pd.DataFrame:
    """Generates microbiome data."""
    np.random.seed(seed)
    shannon_diversity = np.random.uniform(2, 8, size=n_participants)
    df = pd.DataFrame({'shannon_diversity': shannon_diversity})
    return df

def generate_cognitive_scores(n_participants: int, seed: int = 42) -> pd.DataFrame:
    """Generates cognitive scores."""
    np.random.seed(seed)
    cognitive_flexibility_score = np.random.uniform(0, 100, size=n_participants)
    df = pd.DataFrame({'cognitive_flexibility_score': cognitive_flexibility_score})
    return df

def generate_synthetic_cohort(n_participants: int, seed: int = 42) -> pd.DataFrame:
    """Generates a synthetic cohort with all features."""
    demographics = generate_participant_demographics(n_participants, seed)
    lifestyle = generate_lifestyle_factors(n_participants, seed)
    microbiome = generate_microbiome_data(n_participants, seed)
    cognitive = generate_cognitive_scores(n_participants, seed)
    df = pd.concat([demographics, lifestyle, microbiome, cognitive], axis=1)
    return df

def main():
    """Main function to generate and save synthetic data."""
    n_participants = 1000
    seed = 42
    synthetic_data = generate_synthetic_cohort(n_participants, seed)
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    synthetic_data.to_csv(data_dir / "synthetic_data.csv", index=False)
    logging.info(f"Generated synthetic data with {n_participants} participants and saved to data/raw/synthetic_data.csv")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
