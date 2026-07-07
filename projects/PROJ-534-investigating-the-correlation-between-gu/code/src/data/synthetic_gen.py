"""
Synthetic Data Generator for Gut Microbiome and Cognitive Flexibility Study.

This module generates independent (Null Hypothesis) 16S and cognitive data.
It explicitly references Plan Amendment Task 0.1, which mandates that the
initial validation phase uses synthetic data where gut microbiome composition
and cognitive flexibility are statistically independent.

Output:
    data/raw/synthetic_cohort.csv: Merged dataset of participants and microbiome.
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path

# Import shared configuration to ensure consistent seeds and paths
from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR

def generate_synthetic_cohort(
    n_participants: int = 1000,
    n_species: int = 50
) -> pd.DataFrame:
    """
    Generate a synthetic dataset of participants with 16S microbiome profiles
    and cognitive flexibility scores.

    Per Plan Amendment Task 0.1, the 'gut_microbiome' features and 'cognitive_score'
    are generated INDEPENDENTLY to serve as a Null Hypothesis baseline.
    There is NO biological correlation injected between these variables.

    Args:
        n_participants (int): Number of synthetic participants.
        n_species (int): Number of synthetic bacterial species (OTUs/ASVs).

    Returns:
        pd.DataFrame: A DataFrame containing participant metadata,
                      microbiome abundances, and cognitive scores.
    """
    # Set global seed for reproducibility
    np.random.seed(SEED)

    # 1. Generate Participant Metadata
    # Age: Uniformly distributed between 50 and 85 (targeting aging cohort)
    age = np.random.uniform(50, 85, n_participants)

    # Sex: Binary, roughly 50/50
    sex = np.random.choice(['M', 'F'], n_participants)

    # BMI: Normal distribution, mean 27, std 4
    bmi = np.random.normal(27, 4, n_participants)
    bmi = np.clip(bmi, 18.5, 45.0)

    # Fiber Intake (g/day): Normal distribution, mean 15, std 5
    fiber_intake = np.random.normal(15, 5, n_participants)
    fiber_intake = np.clip(fiber_intake, 0, 60)

    # Antibiotic Use (days in past year): Poisson distribution, lambda=3
    antibiotic_use = np.random.poisson(3, n_participants)

    # Cognitive Flexibility Score (0-100): Normal distribution, mean 70, std 10
    # CRITICAL: This is generated INDEPENDENTLY of age, sex, or microbiome.
    cognitive_score = np.random.normal(70, 10, n_participants)
    cognitive_score = np.clip(cognitive_score, 0, 100)

    # 2. Generate Microbiome Data (16S Abundance)
    # Simulate relative abundances for n_species across n_participants
    # Using a Dirichlet distribution to ensure rows sum to 1.0 (relative abundance)
    # Alpha parameter controls the sparsity/diversity.
    alpha = np.ones(n_species) * 0.5  # Sparse distribution
    microbiome_matrix = np.random.dirichlet(alpha, n_participants)

    # Convert to DataFrame
    species_cols = [f"species_{i:03d}" for i in range(n_species)]
    microbiome_df = pd.DataFrame(microbiome_matrix, columns=species_cols)

    # 3. Assemble Final DataFrame
    participant_df = pd.DataFrame({
        'participant_id': [f"PID_{i:05d}" for i in range(n_participants)],
        'age': age,
        'sex': sex,
        'bmi': bmi,
        'fiber_intake': fiber_intake,
        'antibiotic_use': antibiotic_use,
        'cognitive_score': cognitive_score
    })

    # Merge metadata with microbiome data
    full_cohort = pd.concat([participant_df, microbiome_df], axis=1)

    # Add a timestamp for provenance
    full_cohort['generated_at'] = pd.Timestamp.now()

    return full_cohort

def main():
    """
    Main entry point to generate and save the synthetic dataset.
    Ensures output directory exists and writes the CSV file.
    """
    print(f"Starting synthetic data generation (Seed: {SEED})...")
    print("Reference: Plan Amendment Task 0.1 (Null Hypothesis: Independent variables)")

    # Ensure directories exist
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DATA_DIR / "synthetic_cohort.csv"

    # Generate data
    df = generate_synthetic_cohort(n_participants=1000, n_species=50)

    # Save to disk
    df.to_csv(output_path, index=False)

    print(f"Successfully generated {len(df)} participants.")
    print(f"Output saved to: {output_path}")
    print(f"Columns: {list(df.columns)}")

if __name__ == "__main__":
    main()
