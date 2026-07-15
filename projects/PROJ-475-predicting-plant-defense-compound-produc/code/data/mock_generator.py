"""
Deterministic Mock Data Generator for CI and Testing.
Generates synthetic but consistent data to allow pipeline execution without external dependencies.
This module satisfies the 'no manual key injection' constraint by providing a fallback
data source when verified URLs are not configured, ensuring the pipeline can run in CI.
"""
import json
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import sys

from utils.logging import get_module_logger

logger = get_module_logger(__name__)

# Configuration for mock data
NUM_POPULATIONS = 50
NUM_SNPS = 100
NUM_ENV_VARS = 5
SEED = 42

def generate_deterministic_population_ids(n: int) -> List[str]:
    """Generates deterministic population IDs."""
    ids = []
    for i in range(n):
        h = hashlib.sha256(f"pop-{i}-{SEED}".encode()).hexdigest()[:8]
        ids.append(f"POP-{h}")
    return ids

def generate_deterministic_env_ids(n: int) -> List[str]:
    """Generates deterministic environmental IDs."""
    ids = []
    for i in range(n):
        h = hashlib.sha256(f"env-{i}-{SEED}".encode()).hexdigest()[:8]
        ids.append(f"ENV-{h}")
    return ids

def generate_deterministic_compound_ids(n: int) -> List[str]:
    """Generates deterministic compound IDs."""
    ids = []
    for i in range(n):
        h = hashlib.sha256(f"comp-{i}-{SEED}".encode()).hexdigest()[:8]
        ids.append(f"COMP-{h}")
    return ids

def generate_mock_genomic_data() -> pd.DataFrame:
    """Generates mock genomic data."""
    logger.info(f"Generating mock genomic data for {NUM_POPULATIONS} populations.")
    np.random.seed(SEED)
    
    population_ids = generate_deterministic_population_ids(NUM_POPULATIONS)
    snp_cols = [f"SNP_{i}" for i in range(NUM_SNPS)]
    
    # Generate genotype data (0, 1, 2) with some missingness (5%)
    data = np.random.choice([0, 1, 2, np.nan], size=(NUM_POPULATIONS, NUM_SNPS), p=[0.3, 0.4, 0.25, 0.05])
    
    df = pd.DataFrame(data, columns=snp_cols)
    df.insert(0, 'population_id', population_ids)
    
    # Introduce some high missingness rows (>20%) for T015 testing
    if NUM_POPULATIONS > 5:
        high_missing_idx = np.random.choice(NUM_POPULATIONS, size=3, replace=False)
        for idx in high_missing_idx:
            # Set 30% of columns to NaN
            num_missing = int(NUM_SNPS * 0.3)
            missing_cols = np.random.choice(NUM_SNPS, size=num_missing, replace=False)
            df.iloc[idx, missing_cols + 1] = np.nan # +1 for population_id col
    
    return df

def generate_mock_environmental_data() -> pd.DataFrame:
    """Generates mock environmental data."""
    logger.info(f"Generating mock environmental data for {NUM_POPULATIONS} populations.")
    np.random.seed(SEED + 1)
    
    population_ids = generate_deterministic_population_ids(NUM_POPULATIONS)
    env_cols = [f"ENV_VAR_{i}" for i in range(NUM_ENV_VARS)]
    
    data = np.random.normal(loc=50, scale=10, size=(NUM_POPULATIONS, NUM_ENV_VARS))
    
    df = pd.DataFrame(data, columns=env_cols)
    df.insert(0, 'population_id', population_ids)
    df.insert(1, 'source_study', np.random.choice(['Study_A', 'Study_B'], size=NUM_POPULATIONS))
    
    return df

def generate_mock_compound_data() -> pd.DataFrame:
    """Generates mock compound data."""
    logger.info(f"Generating mock compound data for {NUM_POPULATIONS} populations.")
    np.random.seed(SEED + 2)
    
    population_ids = generate_deterministic_population_ids(NUM_POPULATIONS)
    
    # Simulate compound concentration
    concentration = np.random.normal(loc=100, scale=20, size=NUM_POPULATIONS)
    
    df = pd.DataFrame({
        'population_id': population_ids,
        'compound_concentration': concentration,
        'compound_id': generate_deterministic_compound_ids(NUM_POPULATIONS)
    })
    
    return df

def generate_all_mock_data() -> Dict[str, pd.DataFrame]:
    """Generates all mock datasets."""
    genomic = generate_mock_genomic_data()
    env = generate_mock_environmental_data()
    compound = generate_mock_compound_data()
    
    return {
        'genomic': genomic,
        'environmental': env,
        'compound': compound
    }

def main():
    """
    Entry point to generate and save mock data.
    Writes artifacts to data/raw/ and data/processed/ as required by the pipeline.
    """
    logger.info("Starting mock data generation.")
    
    # Ensure directories exist
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    data = generate_all_mock_data()
    
    # Save raw data
    data['genomic'].to_json('data/raw/genomic_vcf.json', orient='records', indent=2)
    data['environmental'].to_json('data/raw/env_data.json', orient='records', indent=2)
    data['compound'].to_json('data/raw/compound_data.json', orient='records', indent=2)
    
    # Merge for validation step (simplified for mock)
    # Join on population_id
    df_merged = data['genomic'].merge(data['environmental'], on='population_id', how='inner')
    df_merged = df_merged.merge(data['compound'], on='population_id', how='inner')
    
    # Save validated data
    df_merged.to_csv('data/processed/validated.csv', index=False)
    
    logger.info(f"Mock data generated and saved. Rows: {len(df_merged)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())