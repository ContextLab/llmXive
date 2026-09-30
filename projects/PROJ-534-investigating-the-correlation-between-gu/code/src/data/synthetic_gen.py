import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Any
import logging

from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR, ensure_directories, set_global_seed

logger = logging.getLogger(__name__)

def generate_participant_demographics(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate participant demographic data.
    Fields: participant_id, age, sex.
    """
    participant_ids = [f"SUBJ_{i:05d}" for i in range(1, n + 1)]
    
    # Age: Normal distribution centered around 70 (aging cohort), clipped to [60, 90]
    ages = rng.normal(loc=70, scale=6, size=n).astype(int)
    ages = np.clip(ages, 60, 90)
    
    # Sex: 50/50 split
    sexes = rng.choice(["M", "F"], size=n)
    
    df = pd.DataFrame({
        "participant_id": participant_ids,
        "age": ages,
        "sex": sexes
    })
    return df

def generate_lifestyle_factors(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate lifestyle factors.
    Fields: bmi, dietary_fiber, antibiotic_use.
    """
    n = len(df)
    
    # BMI: Normal distribution, clipped to realistic range
    bmis = rng.normal(loc=27.0, scale=4.0, size=n).astype(float)
    bmis = np.clip(bmis, 18.5, 45.0)
    
    # Dietary Fiber (g/day): Normal distribution
    dietary_fibers = rng.normal(loc=25.0, scale=10.0, size=n).astype(float)
    dietary_fibers = np.clip(dietary_fibers, 0.0, 60.0)
    
    # Antibiotic use: Bernoulli (approx 15% prevalence in this cohort)
    antibiotic_uses = rng.choice([True, False], size=n, p=[0.15, 0.85])
    
    df["bmi"] = bmis
    df["dietary_fiber"] = dietary_fibers
    df["antibiotic_use"] = antibiotic_uses
    return df

def generate_microbiome_data(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate microbiome alpha diversity metrics.
    Fields: shannon_diversity, simpson_diversity, chao1.
    
    NOTE: These are generated INDEPENDENTLY of cognitive scores to satisfy the Null Hypothesis.
    They are correlated with lifestyle factors (fiber, antibiotics) to simulate realistic biology,
    but NOT with the cognitive outcome.
    """
    n = len(df)
    
    # Shannon Diversity: Normal distribution, typical range 2.5 - 4.5
    shannon = rng.normal(loc=3.5, scale=0.6, size=n).astype(float)
    shannon = np.clip(shannon, 1.5, 5.5)
    
    # Simpson Diversity: Derived roughly from Shannon but with noise
    # Simpson = 1 - (1 / exp(Shannon)) roughly, plus noise
    simpson_base = 1.0 - (1.0 / np.exp(shannon))
    simpson = simpson_base + rng.normal(0, 0.05, size=n)
    simpson = np.clip(simpson, 0.0, 1.0)
    
    # Chao1: Richness estimator, correlated with Shannon but independent of cognition
    chao1 = rng.normal(loc=40.0, scale=10.0, size=n).astype(float)
    chao1 = np.clip(chao1, 10.0, 100.0)
    
    # Apply slight biological constraints: higher fiber -> slightly higher diversity
    fiber_effect = (df["dietary_fiber"].values - 25) * 0.01
    shannon = shannon + fiber_effect
    shannon = np.clip(shannon, 1.5, 5.5)
    
    # Antibiotics -> lower diversity
    antibiotic_effect = df["antibiotic_use"].astype(int).values * -0.3
    shannon = shannon + antibiotic_effect
    shannon = np.clip(shannon, 1.5, 5.5)
    
    df["shannon_diversity"] = shannon
    df["simpson_diversity"] = simpson
    df["chao1"] = chao1
    return df

def generate_cognitive_scores(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate cognitive flexibility scores.
    Field: cognitive_flexibility_score.
    
    CRITICAL: This is generated INDEPENDENTLY of microbiome metrics (shannon, simpson, chao1).
    It may correlate with age (decline) and BMI, but NOT with diversity metrics.
    This ensures the Null Hypothesis (no correlation) holds.
    """
    n = len(df)
    
    # Base score
    base_score = 100.0
    
    # Age effect: Slight decline with age
    age_effect = (df["age"].values - 70) * -0.5
    
    # BMI effect: Slight non-linear effect (U-shaped), simplified here to linear for noise
    bmi_effect = (df["bmi"].values - 27) * -0.2
    
    # Random noise
    noise = rng.normal(loc=0, scale=10.0, size=n)
    
    cognitive_scores = base_score + age_effect + bmi_effect + noise
    
    # Clamp to realistic range (0-150)
    cognitive_scores = np.clip(cognitive_scores, 20.0, 150.0)
    
    df["cognitive_flexibility_score"] = cognitive_scores
    return df

def generate_synthetic_cohort(n_participants: int = 1000) -> pd.DataFrame:
    """
    Generate the full synthetic cohort dataset.
    """
    logger.info(f"Generating synthetic cohort with {n_participants} participants.")
    set_global_seed(SEED)
    rng = np.random.default_rng(SEED)
    
    # Step 1: Demographics
    df = generate_participant_demographics(n_participants, rng)
    
    # Step 2: Lifestyle
    df = generate_lifestyle_factors(df, rng)
    
    # Step 3: Microbiome (Independent of Cognition)
    df = generate_microbiome_data(df, rng)
    
    # Step 4: Cognition (Independent of Microbiome)
    df = generate_cognitive_scores(df, rng)
    
    # Reorder columns to match schema expectation
    columns = [
        "participant_id", "age", "sex", "bmi", 
        "cognitive_flexibility_score", 
        "shannon_diversity", "simpson_diversity", "chao1",
        "dietary_fiber", "antibiotic_use"
    ]
    df = df[columns]
    
    logger.info("Synthetic cohort generation complete.")
    return df

def main():
    """
    Entry point for generating synthetic data.
    Outputs to data/raw/synthetic_data.csv
    """
    ensure_directories()
    
    output_path = RAW_DATA_DIR / "synthetic_data.csv"
    
    if output_path.exists():
        logger.warning(f"Output file {output_path} already exists. Overwriting.")
    
    try:
        df = generate_synthetic_cohort(n_participants=1000)
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote synthetic data to {output_path}")
        print(f"Generated {len(df)} rows to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        raise

if __name__ == "__main__":
    main()
