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

logger = logging.getLogger(__name__)

def generate_participant_demographics(n_participants: int, seed: int = SEED) -> pd.DataFrame:
    """Generate participant demographic data."""
    set_global_seed(seed)
    
    participant_ids = [f"P{str(i).zfill(5)}" for i in range(n_participants)]
    
    # Age: Normal distribution centered around 70, min 65, max 90
    ages = np.random.normal(loc=72, scale=5, size=n_participants)
    ages = np.clip(ages, 65, 90).astype(int)
    
    # Sex: Equal distribution
    sexes = np.random.choice(['male', 'female', 'other'], size=n_participants, p=[0.45, 0.45, 0.1])
    
    # BMI: Normal distribution, mean 26, std 4
    bmis = np.random.normal(loc=26, scale=4, size=n_participants)
    bmis = np.clip(bmis, 18, 45)
    
    df = pd.DataFrame({
        'participant_id': participant_ids,
        'age': ages,
        'sex': sexes,
        'bmi': bmis
    })
    
    return df

def generate_lifestyle_factors(n_participants: int, seed: int = SEED) -> pd.DataFrame:
    """Generate lifestyle factor data."""
    set_global_seed(seed)
    
    # Dietary fiber intake: Normal distribution, mean 25g, std 10g
    fiber_intake = np.random.normal(loc=25, scale=10, size=n_participants)
    fiber_intake = np.clip(fiber_intake, 5, 60)
    
    # Antibiotic use history: Binary, ~20% prevalence
    antibiotic_use = np.random.choice([True, False], size=n_participants, p=[0.2, 0.8])
    
    return pd.DataFrame({
        'dietary_fiber_intake': fiber_intake,
        'antibiotic_use_history': antibiotic_use
    })

def generate_microbiome_data(n_participants: int, n_otus: int = 100, seed: int = SEED) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate synthetic microbiome data with independent diversity metrics.
    
    Creates Shannon, Simpson, and Chao1 indices as independent normal variables
    to ensure no correlation with cognitive scores in the null hypothesis.
    """
    set_global_seed(seed)
    
    participant_ids = [f"P{str(i).zfill(5)}" for i in range(n_participants)]
    
    # Generate alpha diversity metrics as independent normal distributions
    # These are explicitly independent of cognitive scores
    shannon_diversity = np.random.normal(loc=3.5, scale=0.8, size=n_participants)
    simpson_diversity = np.random.normal(loc=0.85, scale=0.1, size=n_participants)
    chao1 = np.random.normal(loc=45, scale=15, size=n_participants)
    
    # Ensure positive values
    shannon_diversity = np.clip(shannon_diversity, 1.0, 6.0)
    simpson_diversity = np.clip(simpson_diversity, 0.5, 0.99)
    chao1 = np.clip(chao1, 10, 100)
    
    alpha_df = pd.DataFrame({
        'participant_id': participant_ids,
        'shannon_diversity': shannon_diversity,
        'simpson_diversity': simpson_diversity,
        'chao1': chao1
    })
    
    # Generate OTU table (sparse count matrix)
    otu_counts = np.random.poisson(lam=50, size=(n_participants, n_otus))
    otu_df = pd.DataFrame(
        otu_counts,
        columns=[f"OTU_{str(i).zfill(5)}" for i in range(n_otus)],
        index=participant_ids
    )
    otu_df.index.name = 'participant_id'
    
    return alpha_df, otu_df

def generate_cognitive_scores(n_participants: int, seed: int = SEED) -> pd.DataFrame:
    """Generate cognitive flexibility scores as independent normal distribution.
    
    This score is generated independently from microbiome metrics to satisfy
    the null hypothesis requirement (no correlation).
    """
    set_global_seed(seed)
    
    participant_ids = [f"P{str(i).zfill(5)}" for i in range(n_participants)]
    
    # Cognitive flexibility score: Normal distribution, mean 50, std 15
    # Independent from microbiome data
    cognitive_scores = np.random.normal(loc=50, scale=15, size=n_participants)
    cognitive_scores = np.clip(cognitive_scores, 0, 100)
    
    return pd.DataFrame({
        'participant_id': participant_ids,
        'cognitive_flexibility_score': cognitive_scores
    })

def generate_synthetic_cohort(n_participants: int = 500, seed: int = SEED) -> pd.DataFrame:
    """Generate the complete synthetic cohort by merging all data sources."""
    set_global_seed(seed)
    
    logger.info(f"Generating synthetic cohort with {n_participants} participants")
    
    demographics = generate_participant_demographics(n_participants, seed)
    lifestyle = generate_lifestyle_factors(n_participants, seed)
    alpha_diversity, otu_table = generate_microbiome_data(n_participants, seed)
    cognitive = generate_cognitive_scores(n_participants, seed)
    
    # Merge all dataframes
    merged = demographics.merge(lifestyle, left_index=True, right_index=True)
    merged = merged.merge(alpha_diversity, on='participant_id')
    merged = merged.merge(cognitive, on='participant_id')
    
    # Ensure correct data types as per schema
    merged['participant_id'] = merged['participant_id'].astype(str)
    merged['age'] = merged['age'].astype(int)
    merged['sex'] = merged['sex'].astype(str)
    merged['bmi'] = merged['bmi'].astype(float)
    merged['cognitive_flexibility_score'] = merged['cognitive_flexibility_score'].astype(float)
    merged['shannon_diversity'] = merged['shannon_diversity'].astype(float)
    merged['simpson_diversity'] = merged['simpson_diversity'].astype(float)
    merged['chao1'] = merged['chao1'].astype(float)
    merged['dietary_fiber_intake'] = merged['dietary_fiber_intake'].astype(float)
    merged['antibiotic_use_history'] = merged['antibiotic_use_history'].astype(bool)
    
    logger.info("Synthetic cohort generation complete")
    return merged, otu_table

def main():
    """Main entry point to generate synthetic data and save to disk."""
    ensure_directories()
    set_global_seed(SEED)
    
    logger.info("Starting synthetic data generation")
    
    # Generate cohort
    cohort_df, otu_table = generate_synthetic_cohort(n_participants=500)
    
    # Save CSV
    csv_path = get_raw_data_dir() / "synthetic_data.csv"
    cohort_df.to_csv(csv_path, index=False)
    logger.info(f"Saved synthetic data to {csv_path}")
    
    # Save OTU table as BIOM-like format (TSV for simplicity, can be converted)
    biom_path = get_raw_data_dir() / "feature_table.biom"
    otu_table.to_csv(biom_path, sep='\t')
    logger.info(f"Saved feature table to {biom_path}")
    
    logger.info("Synthetic data generation completed successfully")
    return csv_path, biom_path

if __name__ == "__main__":
    main()
