"""
Mock Data Generator for CI and Testing.
Generates deterministic mock genomic, environmental, and compound data.
"""
import json
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.logging import get_module_logger

logger = get_module_logger(__name__)

# Seed for determinism
SEED = 42
np.random.seed(SEED)

def generate_deterministic_population_ids(count: int) -> List[str]:
    """Generates deterministic population IDs."""
    ids = []
    for i in range(count):
        h = hashlib.sha256(f"pop_{i}_{SEED}".encode()).hexdigest()[:8]
        ids.append(f"POP_{h}")
    return ids

def generate_deterministic_env_ids(count: int) -> List[str]:
    """Generates deterministic environment IDs."""
    ids = []
    for i in range(count):
        h = hashlib.sha256(f"env_{i}_{SEED}".encode()).hexdigest()[:8]
        ids.append(f"ENV_{h}")
    return ids

def generate_deterministic_compound_ids(count: int) -> List[str]:
    """Generates deterministic compound IDs."""
    ids = []
    for i in range(count):
        h = hashlib.sha256(f"comp_{i}_{SEED}".encode()).hexdigest()[:8]
        ids.append(f"COMP_{h}")
    return ids

def generate_mock_genomic_data(n_populations: int = 50, n_snps: int = 100) -> List[Dict]:
    """
    Generates mock genomic data.
    Returns a list of dictionaries, one per population-SNP combination.
    """
    pop_ids = generate_deterministic_population_ids(n_populations)
    env_ids = generate_deterministic_env_ids(n_populations)
    compound_ids = generate_deterministic_compound_ids(n_populations)
    
    data = []
    for i in range(n_populations):
        pop_id = pop_ids[i]
        env_id = env_ids[i]
        comp_id = compound_ids[i]
        
        # Generate SNPs
        for j in range(n_snps):
            snp_id = f"SNP_{j}"
            # Random genotype (0, 1, 2) with some missingness
            if np.random.random() < 0.05: # 5% missing
                genotype = None
            else:
                genotype = np.random.choice([0, 1, 2], p=[0.5, 0.3, 0.2])
            
            data.append({
                'population_id': pop_id,
                'env_id': env_id,
                'compound_id': comp_id,
                'snp_id': snp_id,
                'genotype': genotype
            })
    
    return data

def generate_mock_environmental_data(n_populations: int = 50) -> List[Dict]:
    """
    Generates mock environmental data.
    Returns a list of dictionaries, one per population.
    """
    pop_ids = generate_deterministic_population_ids(n_populations)
    env_ids = generate_deterministic_env_ids(n_populations)
    compound_ids = generate_deterministic_compound_ids(n_populations)
    
    data = []
    for i in range(n_populations):
        pop_id = pop_ids[i]
        env_id = env_ids[i]
        comp_id = compound_ids[i]
        
        # Random environmental variables
        temp = np.random.normal(20, 5)
        precip = np.random.normal(1000, 200)
        soil_ph = np.random.normal(6.5, 1.0)
        
        # Some missingness (10%)
        if np.random.random() < 0.1:
            temp = None
        
        data.append({
            'population_id': pop_id,
            'env_id': env_id,
            'compound_id': comp_id,
            'temperature': temp,
            'precipitation': precip,
            'soil_ph': soil_ph
        })
    
    return data

def generate_mock_compound_data(n_populations: int = 50) -> List[Dict]:
    """
    Generates mock compound data.
    Returns a list of dictionaries, one per population.
    """
    pop_ids = generate_deterministic_population_ids(n_populations)
    env_ids = generate_deterministic_env_ids(n_populations)
    compound_ids = generate_deterministic_compound_ids(n_populations)
    
    data = []
    for i in range(n_populations):
        pop_id = pop_ids[i]
        env_id = env_ids[i]
        comp_id = compound_ids[i]
        
        # Random compound concentration
        concentration = np.random.lognormal(mean=2, sigma=0.5)
        
        data.append({
            'population_id': pop_id,
            'env_id': env_id,
            'compound_id': comp_id,
            'concentration': concentration
        })
    
    return data

def generate_all_mock_data() -> Dict[str, List[Dict]]:
    """Generates all mock data types."""
    logger.info("Generating all mock data.")
    return {
        'genomic': generate_mock_genomic_data(),
        'environmental': generate_mock_environmental_data(),
        'compound': generate_mock_compound_data()
    }

def main():
    """Entry point for mock generator (debugging)."""
    data = generate_all_mock_data()
    logger.info(f"Generated {len(data['genomic'])} genomic records, {len(data['environmental'])} env records, {len(data['compound'])} compound records.")

if __name__ == "__main__":
    main()
