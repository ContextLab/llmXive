"""
Synthetic Data Generator for Gut Microbiome and Cognitive Flexibility Study.

This module generates independent (Null Hypothesis) 16S and cognitive data.
Explicitly references Plan Amendment Task 0.1 which mandates that for the
validation phase, all data must be statistically independent to verify the
pipeline does not produce false positives.

The generator creates:
1. Participant Demographics (Age, Sex)
2. Lifestyle Factors (BMI, Fiber intake, Antibiotic usage)
3. Microbiome Data (OTU counts for Shannon/Simpson calculation)
4. Cognitive Scores (Flexibility metrics)

Crucially, in this Null Hypothesis mode, the microbiome composition and
cognitive scores are generated from independent distributions. Any observed
correlation in downstream analysis should be statistically insignificant (p > 0.05).
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any
import logging

from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_participant_demographics(n_participants: int, seed: int) -> pd.DataFrame:
    """
    Generate participant demographic data.

    Args:
        n_participants: Number of participants to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: participant_id, age, sex.
    """
    np.random.seed(seed)
    logger.info(f"Generating demographics for {n_participants} participants with seed {seed}")

    participant_ids = [f"PID_{i:04d}" for i in range(n_participants)]

    # Age: Uniform distribution between 60 and 85 to focus on aging cohort
    # This ensures we have a mix of ages for filtering (US1 requires age >= 65)
    ages = np.random.randint(60, 86, size=n_participants)

    # Sex: 50/50 split
    sexes = np.random.choice(['M', 'F'], size=n_participants)

    df = pd.DataFrame({
        'participant_id': participant_ids,
        'age': ages,
        'sex': sexes
    })

    return df

def generate_lifestyle_factors(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """
    Generate lifestyle factors (BMI, Fiber, Antibiotics).

    These are generated independently of microbiome and cognitive scores
    to satisfy the Null Hypothesis requirement (Plan Amendment Task 0.1).

    Args:
        df: Existing participant demographics DataFrame.
        seed: Random seed.

    Returns:
        DataFrame with columns: bmi, fiber_intake, antibiotic_use.
    """
    np.random.seed(seed + 1) # Offset seed slightly for variety but deterministic
    logger.info("Generating lifestyle factors")

    n = len(df)

    # BMI: Normal distribution, mean 26, std 4
    bmi = np.random.normal(26, 4, n).round(1)
    # Ensure positive values
    bmi = np.clip(bmi, 15, 50)

    # Fiber intake: Normal distribution, mean 25g, std 10g
    fiber = np.random.normal(25, 10, n).round(1)
    fiber = np.clip(fiber, 0, 80)

    # Antibiotic use: Binary (0 = No, 1 = Yes)
    # Approx 20% of population has recent antibiotic use
    antibiotics = np.random.choice([0, 1], size=n, p=[0.8, 0.2])

    lifestyle_df = pd.DataFrame({
        'participant_id': df['participant_id'],
        'bmi': bmi,
        'fiber_intake': fiber,
        'antibiotic_use': antibiotics
    })

    return lifestyle_df

def generate_microbiome_data(df: pd.DataFrame, seed: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate microbiome data (OTU table and sample metadata).

    Generates random OTU counts. The composition is independent of cognitive scores.
    This satisfies the Null Hypothesis validation requirement.

    Args:
        df: Participant demographics DataFrame.
        seed: Random seed.

    Returns:
        Tuple of (otu_table, sample_metadata).
        otu_table: Index=participant_id, columns=OTU IDs, values=counts.
        sample_metadata: Index=participant_id, columns=metadata.
    """
    np.random.seed(seed + 2)
    logger.info("Generating microbiome data (independent of cognitive scores)")

    n_participants = len(df)
    n_otus = 50  # Simulate 50 distinct OTUs

    otu_names = [f"OTU_{i:03d}" for i in range(n_otus)]

    # Generate random counts from a Dirichlet-multinomial distribution simulation
    # to mimic over-dispersed count data typical in 16S sequencing
    # We use a simple negative binomial approximation for speed and independence
    counts = np.random.negative_binomial(n=10, p=0.3, size=(n_participants, n_otus)) + 1

    otu_df = pd.DataFrame(
        counts,
        index=df['participant_id'],
        columns=otu_names
    )

    # Metadata for microbiome samples
    sample_meta = pd.DataFrame({
        'participant_id': df['participant_id'],
        'sequencing_depth': np.random.randint(10000, 50000, n_participants)
    }, index=df['participant_id'])

    return otu_df, sample_meta

def generate_cognitive_scores(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """
    Generate cognitive flexibility scores.

    Generates scores from a normal distribution independent of microbiome data.
    This ensures the Null Hypothesis (no correlation) holds.

    Args:
        df: Participant demographics DataFrame.
        seed: Random seed.

    Returns:
        DataFrame with columns: cognitive_score, reaction_time.
    """
    np.random.seed(seed + 3)
    logger.info("Generating cognitive scores (independent of microbiome)")

    n = len(df)

    # Cognitive Score: Normal distribution, mean 100, std 15
    # Range roughly 55 to 145
    cognitive_score = np.random.normal(100, 15, n)
    cognitive_score = np.clip(cognitive_score, 40, 160).round(2)

    # Reaction Time: Normal distribution, mean 500ms, std 100ms
    reaction_time = np.random.normal(500, 100, n)
    reaction_time = np.clip(reaction_time, 200, 1000).round(2)

    cognitive_df = pd.DataFrame({
        'participant_id': df['participant_id'],
        'cognitive_score': cognitive_score,
        'reaction_time': reaction_time
    })

    return cognitive_df

def generate_synthetic_cohort(n_participants: int = 1000, seed: int = SEED) -> Dict[str, pd.DataFrame]:
    """
    Orchestrates the generation of the full synthetic cohort.

    This function implements Plan Amendment Task 0.1 by ensuring all
    generated variables (Microbiome, Cognitive) are statistically independent.
    No causal links are introduced in this phase.

    Args:
        n_participants: Total number of participants.
        seed: Global random seed.

    Returns:
        Dictionary containing:
            'demographics': DataFrame
            'lifestyle': DataFrame
            'microbiome_otu': DataFrame (OTU counts)
            'microbiome_meta': DataFrame
            'cognitive': DataFrame
    """
    logger.info(f"Starting synthetic cohort generation for {n_participants} participants.")

    # 1. Demographics
    demographics = generate_participant_demographics(n_participants, seed)

    # 2. Lifestyle
    lifestyle = generate_lifestyle_factors(demographics, seed)

    # 3. Microbiome
    otu_table, micro_meta = generate_microbiome_data(demographics, seed)

    # 4. Cognitive
    cognitive = generate_cognitive_scores(demographics, seed)

    return {
        'demographics': demographics,
        'lifestyle': lifestyle,
        'microbiome_otu': otu_table,
        'microbiome_meta': micro_meta,
        'cognitive': cognitive
    }

def main():
    """
    Main entry point to generate and save synthetic data to disk.
    """
    # Ensure directories exist
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving synthetic data to {RAW_DATA_DIR}")

    # Generate data
    # Using a fixed seed for reproducibility as per config
    data = generate_synthetic_cohort(n_participants=1000, seed=SEED)

    # Save individual components
    # Demographics
    demographics_path = RAW_DATA_DIR / "demographics.csv"
    data['demographics'].to_csv(demographics_path, index=False)
    logger.info(f"Saved demographics to {demographics_path}")

    # Lifestyle
    lifestyle_path = RAW_DATA_DIR / "lifestyle.csv"
    data['lifestyle'].to_csv(lifestyle_path, index=False)
    logger.info(f"Saved lifestyle to {lifestyle_path}")

    # Microbiome OTU Table
    otu_path = RAW_DATA_DIR / "otu_table.csv"
    data['microbiome_otu'].to_csv(otu_path)
    logger.info(f"Saved OTU table to {otu_path}")

    # Microbiome Metadata
    micro_meta_path = RAW_DATA_DIR / "microbiome_metadata.csv"
    data['microbiome_meta'].to_csv(micro_meta_path, index=False)
    logger.info(f"Saved microbiome metadata to {micro_meta_path}")

    # Cognitive Scores
    cognitive_path = RAW_DATA_DIR / "cognitive_scores.csv"
    data['cognitive'].to_csv(cognitive_path, index=False)
    logger.info(f"Saved cognitive scores to {cognitive_path}")

    logger.info("Synthetic cohort generation complete.")

if __name__ == "__main__":
    main()