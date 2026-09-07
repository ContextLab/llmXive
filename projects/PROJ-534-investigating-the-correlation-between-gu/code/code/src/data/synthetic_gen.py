"""
Synthetic Data Generation for Gut Microbiome and Cognitive Flexibility Study.

This module generates independent (Null Hypothesis) 16S and cognitive data.
It explicitly implements Plan Amendment Task 0.1 by ensuring NO correlation
exists between the generated microbiome features and cognitive scores.
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any

# Import shared configuration
from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR

# Ensure reproducibility
np.random.seed(SEED)


def generate_participant_demographics(n_participants: int = 1000) -> pd.DataFrame:
    """
    Generate participant demographics including age, sex, and BMI.
    
    Args:
        n_participants: Number of participants to generate.
        
    Returns:
        DataFrame with participant demographics.
    """
    ids = [f"PID_{i:04d}" for i in range(n_participants)]
    
    # Age: Normal distribution centered at 70, truncated to realistic range [50, 90]
    ages = np.random.normal(loc=70, scale=8, size=n_participants)
    ages = np.clip(ages, 50, 90).astype(int)
    
    # Sex: Binary (0: Female, 1: Male) with roughly 50/50 split
    sex = np.random.choice([0, 1], size=n_participants, p=[0.52, 0.48])
    
    # BMI: Normal distribution, truncated
    bmi = np.random.normal(loc=27, scale=4, size=n_participants)
    bmi = np.clip(bmi, 18, 45).round(1)
    
    return pd.DataFrame({
        "participant_id": ids,
        "age": ages,
        "sex": sex,
        "bmi": bmi
    })


def generate_lifestyle_factors(n_participants: int) -> pd.DataFrame:
    """
    Generate lifestyle factors including fiber intake and antibiotic history.
    
    These are generated INDEPENDENTLY of cognitive scores to satisfy the Null Hypothesis.
    
    Args:
        n_participants: Number of participants.
        
    Returns:
        DataFrame with lifestyle factors.
    """
    # Fiber intake (g/day): Normal distribution, truncated
    fiber = np.random.normal(loc=20, scale=8, size=n_participants)
    fiber = np.clip(fiber, 5, 50).round(1)
    
    # Antibiotics history (last 6 months): Binary (0: No, 1: Yes)
    # Roughly 20% prevalence
    antibiotics = np.random.choice([0, 1], size=n_participants, p=[0.80, 0.20])
    
    return pd.DataFrame({
        "fiber_intake": fiber,
        "antibiotics_history": antibiotics
    })


def generate_microbiome_data(n_participants: int, n_taxa: int = 50) -> pd.DataFrame:
    """
    Generate synthetic 16S microbiome data (OTU counts).
    
    Generates counts from a Dirichlet-Multinomial distribution to mimic
    compositional microbiome data. Crucially, these are generated 
    INDEPENDENTLY of cognitive scores (Null Hypothesis).
    
    Args:
        n_participants: Number of participants.
        n_taxa: Number of taxa (OTUs) to simulate.
        
    Returns:
        DataFrame with participant_id and OTU counts.
    """
    ids = [f"PID_{i:04d}" for i in range(n_participants)]
    
    # Generate base proportions using Dirichlet distribution
    # Alpha parameters control the sparsity and evenness
    alpha = np.ones(n_taxa) * 0.5 
    proportions = np.random.dirichlet(alpha, size=n_participants)
    
    # Convert proportions to counts (simulate sequencing depth ~10k-50k)
    depths = np.random.randint(10000, 50000, size=n_participants)
    counts = (proportions * depths[:, None]).astype(int)
    
    # Ensure no negative counts (shouldn't happen with int conversion, but safe)
    counts = np.maximum(counts, 0)
    
    # Create column names
    otu_cols = [f"OTU_{i:03d}" for i in range(n_taxa)]
    
    df = pd.DataFrame(counts, columns=otu_cols)
    df.insert(0, "participant_id", ids)
    
    return df


def generate_cognitive_scores(n_participants: int) -> pd.DataFrame:
    """
    Generate cognitive flexibility scores.
    
    IMPORTANT: These scores are generated INDEPENDENTLY of the microbiome data
    to satisfy the Null Hypothesis (Plan Amendment Task 0.1). No correlation
    is injected between microbiome composition and cognitive scores.
    
    Args:
        n_participants: Number of participants.
        
    Returns:
        DataFrame with cognitive scores.
    """
    # Cognitive Flexibility Score: Normal distribution, scaled 0-100
    # Mean ~65, SD ~15, truncated to [0, 100]
    scores = np.random.normal(loc=65, scale=15, size=n_participants)
    scores = np.clip(scores, 0, 100).round(2)
    
    # Add a small amount of noise to ensure no exact duplicates
    noise = np.random.normal(0, 0.1, size=n_participants)
    scores = (scores + noise).round(2)
    
    return pd.DataFrame({
        "cognitive_flexibility_score": scores
    })


def generate_synthetic_cohort(n_participants: int = 1000, n_taxa: int = 50) -> pd.DataFrame:
    """
    Generate the full synthetic cohort by combining demographics, lifestyle,
    microbiome, and cognitive data.
    
    This function orchestrates the generation of all data components, ensuring
    they are merged correctly by participant_id.
    
    Args:
        n_participants: Total number of participants to generate.
        n_taxa: Number of OTUs to simulate.
        
    Returns:
        Merged DataFrame containing all generated data.
    """
    # Set seed for reproducibility at the start of generation
    np.random.seed(SEED)
    
    # Generate components independently
    demographics = generate_participant_demographics(n_participants)
    lifestyle = generate_lifestyle_factors(n_participants)
    microbiome = generate_microbiome_data(n_participants, n_taxa)
    cognitive = generate_cognitive_scores(n_participants)
    
    # Merge all dataframes
    cohort = demographics.merge(lifestyle, left_index=True, right_index=True)
    cohort = cohort.merge(microbiome, on="participant_id")
    cohort = cohort.merge(cognitive, left_index=True, right_index=True)
    
    # Reorder columns for logical flow
    cols = ["participant_id", "age", "sex", "bmi", "fiber_intake", 
            "antibiotics_history"] + [col for col in cohort.columns if col not in cols]
    
    return cohort[cols]


def main():
    """
    Main entry point to generate and save the synthetic cohort.
    """
    # Ensure output directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating synthetic cohort with fixed seed {SEED}...")
    print(f"Output directory: {RAW_DATA_DIR}")
    
    # Generate the cohort
    cohort = generate_synthetic_cohort(n_participants=1000, n_taxa=50)
    
    # Save to CSV
    output_path = RAW_DATA_DIR / "synthetic_cohort_raw.csv"
    cohort.to_csv(output_path, index=False)
    
    print(f"Successfully generated {len(cohort)} participants.")
    print(f"Saved raw data to: {output_path}")
    
    # Log summary statistics
    print("\n--- Summary Statistics ---")
    print(f"Age range: {cohort['age'].min()} - {cohort['age'].max()}")
    print(f"Cognitive Score range: {cohort['cognitive_flexibility_score'].min():.2f} - {cohort['cognitive_flexibility_score'].max():.2f}")
    print(f"Number of OTUs: {len([c for c in cohort.columns if c.startswith('OTU_')])}")


if __name__ == "__main__":
    main()