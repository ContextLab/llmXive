"""
Synthetic data generation for the Gut Microbiome and Cognitive Flexibility study.

This module generates a synthetic dataset where cognitive flexibility scores and
microbiome diversity metrics are statistically independent (Null Hypothesis).
All data types strictly adhere to contracts/dataset.schema.yaml.
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any
import logging

from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR, ensure_directories, set_global_seed

# Configure logger
logger = logging.getLogger(__name__)

def generate_participant_demographics(n_participants: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate participant demographics: participant_id, age, sex, bmi.
    
    Args:
        n_participants: Number of participants to generate.
        rng: NumPy random generator for reproducibility.
        
    Returns:
        DataFrame with demographic columns.
    """
    logger.info(f"Generating demographics for {n_participants} participants.")
    
    ids = [f"PID_{i:05d}" for i in range(n_participants)]
    
    # Age: Normal distribution centered at 70 (aging cohort), clipped to realistic bounds
    ages = rng.normal(loc=70, scale=6, size=n_participants)
    ages = np.clip(ages, 60, 90).astype(int)
    
    # Sex: Binary, 50/50 split
    sexes = rng.choice(["M", "F"], size=n_participants)
    
    # BMI: Normal distribution, clipped to realistic bounds
    bmis = rng.normal(loc=26.5, scale=3.5, size=n_participants)
    bmis = np.clip(bmis, 18.5, 45.0).astype(float)
    
    return pd.DataFrame({
        "participant_id": ids,
        "age": ages,
        "sex": sexes,
        "bmi": bmis
    })

def generate_lifestyle_factors(n_participants: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate lifestyle factors: dietary_fiber, antibiotic_use.
    
    Args:
        n_participants: Number of participants.
        rng: NumPy random generator.
        
    Returns:
        DataFrame with lifestyle columns.
    """
    logger.info("Generating lifestyle factors.")
    
    # Dietary fiber (g/day): Normal distribution
    dietary_fiber = rng.normal(loc=25.0, scale=8.0, size=n_participants)
    dietary_fiber = np.clip(dietary_fiber, 5.0, 60.0).astype(float)
    
    # Antibiotic use (bool): Bernoulli trial (approx 20% recent use)
    antibiotic_use = rng.choice([False, True], size=n_participants, p=[0.8, 0.2])
    
    return pd.DataFrame({
        "dietary_fiber": dietary_fiber,
        "antibiotic_use": antibiotic_use
    })

def generate_microbiome_data(n_participants: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate microbiome alpha diversity metrics.
    
    CRITICAL: These are generated INDEPENDENTLY of cognitive scores to satisfy the Null Hypothesis.
    
    Args:
        n_participants: Number of participants.
        rng: NumPy random generator.
        
    Returns:
        DataFrame with diversity metrics.
    """
    logger.info("Generating microbiome diversity metrics (Independent of cognitive scores).")
    
    # Shannon Diversity: Normal distribution, typical range 2.5 - 4.5
    shannon = rng.normal(loc=3.5, scale=0.6, size=n_participants)
    shannon = np.clip(shannon, 1.0, 6.0).astype(float)
    
    # Simpson Diversity: Beta distribution or Normal approximation, range 0-1
    simpson = rng.normal(loc=0.85, scale=0.08, size=n_participants)
    simpson = np.clip(simpson, 0.4, 0.99).astype(float)
    
    # Chao1: Normal distribution, related to richness
    chao1 = rng.normal(loc=150.0, scale=40.0, size=n_participants)
    chao1 = np.clip(chao1, 50.0, 300.0).astype(float)
    
    return pd.DataFrame({
        "shannon_diversity": shannon,
        "simpson_diversity": simpson,
        "chao1": chao1
    })

def generate_cognitive_scores(n_participants: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate cognitive flexibility scores.
    
    CRITICAL: Generated INDEPENDENTLY of microbiome metrics. No correlation is introduced.
    
    Args:
        n_participants: Number of participants.
        rng: NumPy random generator.
        
    Returns:
        DataFrame with cognitive scores.
    """
    logger.info("Generating cognitive flexibility scores (Independent of microbiome).")
    
    # Cognitive Flexibility Score: Normal distribution, typical range 0-100
    # Mean slightly lower for older cohort
    cognitive_scores = rng.normal(loc=65.0, scale=12.0, size=n_participants)
    cognitive_scores = np.clip(cognitive_scores, 20.0, 100.0).astype(float)
    
    return pd.DataFrame({
        "cognitive_flexibility_score": cognitive_scores
    })

def generate_synthetic_cohort(n_participants: int = 500) -> pd.DataFrame:
    """
    Generate the full synthetic cohort dataset.
    
    This function orchestrates the generation of all components and merges them.
    The resulting dataset satisfies the Null Hypothesis: microbiome diversity
    and cognitive flexibility are statistically independent.
    
    Args:
        n_participants: Total number of participants to generate.
        
    Returns:
        Complete DataFrame matching contracts/dataset.schema.yaml.
    """
    logger.info(f"Starting synthetic cohort generation with N={n_participants}.")
    set_global_seed(SEED)
    rng = np.random.default_rng(SEED)
    
    # Generate components
    demographics = generate_participant_demographics(n_participants, rng)
    lifestyle = generate_lifestyle_factors(n_participants, rng)
    microbiome = generate_microbiome_data(n_participants, rng)
    cognitive = generate_cognitive_scores(n_participants, rng)
    
    # Merge all dataframes on index (aligned generation)
    cohort = pd.concat([demographics, lifestyle, microbiome, cognitive], axis=1)
    
    # Ensure correct data types as per schema
    cohort["participant_id"] = cohort["participant_id"].astype(str)
    cohort["age"] = cohort["age"].astype(int)
    cohort["sex"] = cohort["sex"].astype(str)
    cohort["bmi"] = cohort["bmi"].astype(float)
    cohort["dietary_fiber"] = cohort["dietary_fiber"].astype(float)
    cohort["antibiotic_use"] = cohort["antibiotic_use"].astype(bool)
    cohort["shannon_diversity"] = cohort["shannon_diversity"].astype(float)
    cohort["simpson_diversity"] = cohort["simpson_diversity"].astype(float)
    cohort["chao1"] = cohort["chao1"].astype(float)
    cohort["cognitive_flexibility_score"] = cohort["cognitive_flexibility_score"].astype(float)
    
    logger.info(f"Synthetic cohort generated successfully with {len(cohort)} rows.")
    return cohort

def main():
    """
    Main entry point for synthetic data generation.
    Generates data and saves to data/raw/synthetic_data.csv.
    """
    # Ensure directories exist
    ensure_directories()
    
    output_path = RAW_DATA_DIR / "synthetic_data.csv"
    
    # Generate data
    cohort = generate_synthetic_cohort(n_participants=500)
    
    # Save to CSV
    cohort.to_csv(output_path, index=False)
    logger.info(f"Synthetic data saved to {output_path}")
    
    # Log a quick verification of independence
    corr = cohort["shannon_diversity"].corr(cohort["cognitive_flexibility_score"])
    logger.info(f"Verification: Correlation between Shannon and Cognitive Score: {corr:.4f} (Expected ~0.0)")

if __name__ == "__main__":
    main()
