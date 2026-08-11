"""
Synthetic data generation module for the gut microbiome and cognitive flexibility study.

This module generates independent (Null Hypothesis) 16S and cognitive data with fixed seeds.
The data is generated to have NO correlation between microbiome diversity and cognitive scores.
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any

from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR

# Set random seed for reproducibility
np.random.seed(SEED)

def generate_participant_demographics(n_participants: int = 1000) -> pd.DataFrame:
    """
    Generate participant demographics data.

    Args:
        n_participants: Number of participants to generate

    Returns:
        DataFrame with participant demographics
    """
    participant_ids = [f"ID_{i:04d}" for i in range(1, n_participants + 1)]

    # Age: skewed towards older adults (60-90)
    ages = np.random.randint(60, 91, size=n_participants)

    # Sex: roughly equal distribution
    sexes = np.random.choice(['M', 'F'], size=n_participants, p=[0.5, 0.5])

    # BMI: normal distribution around 25
    bmis = np.random.normal(25, 4, size=n_participants)
    bmis = np.clip(bmis, 15, 45)  # Clip to realistic range

    return pd.DataFrame({
        'participant_id': participant_ids,
        'age': ages,
        'sex': sexes,
        'BMI': np.round(bmis, 2)
    })

def generate_lifestyle_factors(n_participants: int) -> pd.DataFrame:
    """
    Generate lifestyle factors data.

    Args:
        n_participants: Number of participants

    Returns:
        DataFrame with lifestyle factors
    """
    # Fiber intake: normal distribution around 20g
    fiber = np.random.normal(20, 8, size=n_participants)
    fiber = np.clip(fiber, 5, 50)  # Clip to realistic range

    # Antibiotic use: Poisson distribution (low frequency)
    antibiotics = np.random.poisson(0.5, size=n_participants)

    return pd.DataFrame({
        'fiber': np.round(fiber, 1),
        'antibiotics': antibiotics
    })

def generate_microbiome_data(n_participants: int) -> pd.DataFrame:
    """
    Generate microbiome data (independent of cognitive scores - Null Hypothesis).

    Args:
        n_participants: Number of participants

    Returns:
        DataFrame with microbiome diversity metrics
    """
    # Generate diversity metrics independently (no correlation with cognitive scores)
    shannon = np.random.normal(3.5, 0.5, size=n_participants)
    shannon = np.clip(shannon, 1.0, 5.0)

    simpson = np.random.normal(0.85, 0.1, size=n_participants)
    simpson = np.clip(simpson, 0.5, 1.0)

    chao1 = np.random.normal(150, 30, size=n_participants)
    chao1 = np.clip(chao1, 50, 300)

    return pd.DataFrame({
        'shannon_diversity': np.round(shannon, 3),
        'simpson_diversity': np.round(simpson, 3),
        'chao1': np.round(chao1, 1)
    })

def generate_cognitive_scores(n_participants: int) -> pd.DataFrame:
    """
    Generate cognitive scores (independent of microbiome data - Null Hypothesis).

    Args:
        n_participants: Number of participants

    Returns:
        DataFrame with cognitive scores
    """
    # Cognitive scores: normal distribution around 75
    cognitive = np.random.normal(75, 10, size=n_participants)
    cognitive = np.clip(cognitive, 30, 100)

    return pd.DataFrame({
        'cognitive_score': np.round(cognitive, 2)
    })

def generate_synthetic_cohort(n_participants: int = 1000) -> pd.DataFrame:
    """
    Generate the complete synthetic cohort with independent variables.

    This function generates data where microbiome diversity and cognitive scores
    are statistically independent (Null Hypothesis).

    Args:
        n_participants: Number of participants to generate

    Returns:
        DataFrame with complete synthetic cohort
    """
    # Generate all components
    demographics = generate_participant_demographics(n_participants)
    lifestyle = generate_lifestyle_factors(n_participants)
    microbiome = generate_microbiome_data(n_participants)
    cognitive = generate_cognitive_scores(n_participants)

    # Merge all components
    cohort = pd.concat([demographics, lifestyle, microbiome, cognitive], axis=1)

    return cohort

def main():
    """
    Main entry point for synthetic data generation.

    Generates the synthetic cohort and saves it to data/raw/synthetic_cohort.csv.
    """
    n_participants = 1000
    output_path = RAW_DATA_DIR / "synthetic_cohort.csv"

    print(f"Generating synthetic cohort with {n_participants} participants...")
    cohort = generate_synthetic_cohort(n_participants)

    print(f"Saving to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cohort.to_csv(output_path, index=False)

    print(f"Generated {len(cohort)} rows")
    print(f"Columns: {list(cohort.columns)}")
    print(f"Age range: {cohort['age'].min()} - {cohort['age'].max()}")
    print(f"Shannon range: {cohort['shannon_diversity'].min():.2f} - {cohort['shannon_diversity'].max():.2f}")
    print(f"Cognitive range: {cohort['cognitive_score'].min():.2f} - {cohort['cognitive_score'].max():.2f}")

    return cohort

if __name__ == "__main__":
    main()
