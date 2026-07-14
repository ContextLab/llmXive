"""
Mock Data Generator for CI and Fallback.

Generates deterministic mock genomic, environmental, and compound data.
This module satisfies the requirement for a 'no manual key injection' constraint
by providing a fully self-contained, reproducible dataset generator.
"""

import json
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Seed for deterministic generation
MOCK_SEED = 42

def _get_deterministic_random(seed: int, length: int) -> np.ndarray:
    """Generates a deterministic random array based on seed."""
    rng = np.random.default_rng(seed)
    return rng.random(length)

def generate_deterministic_population_ids(n: int, seed: int = MOCK_SEED) -> List[str]:
    """Generates deterministic population IDs."""
    ids = []
    for i in range(n):
        # Create a deterministic ID based on index and seed
        h = hashlib.sha256(f"{seed}-pop-{i}".encode()).hexdigest()[:8]
        ids.append(f"POP_{h}")
    return ids

def generate_deterministic_env_ids(n: int, seed: int = MOCK_SEED) -> List[str]:
    """Generates deterministic environment IDs."""
    ids = []
    for i in range(n):
        h = hashlib.sha256(f"{seed}-env-{i}".encode()).hexdigest()[:8]
        ids.append(f"ENV_{h}")
    return ids

def generate_deterministic_compound_ids(n: int, seed: int = MOCK_SEED) -> List[str]:
    """Generates deterministic compound IDs."""
    ids = []
    for i in range(n):
        h = hashlib.sha256(f"{seed}-cmp-{i}".encode()).hexdigest()[:8]
        ids.append(f"CMP_{h}")
    return ids

def generate_mock_genomic_data(n_samples: int = 100, n_snps: int = 50) -> Dict[str, Any]:
    """
    Generates mock genomic VCF-like data.
    
    Returns a dictionary structured to mimic a simplified VCF JSON representation.
    """
    np.random.seed(MOCK_SEED)
    
    pop_ids = generate_deterministic_population_ids(n_samples)
    
    # Simulate genotype matrix (0, 1, 2 for homozygous ref, heterozygous, homozygous alt)
    # Shape: (n_samples, n_snps)
    genotype_matrix = np.random.randint(0, 3, size=(n_samples, n_snps))
    
    # Simulate SNP positions and IDs
    snp_ids = [f"rs{10000000 + i}" for i in range(n_snps)]
    positions = np.random.randint(1000, 1000000, size=n_snps)
    
    data = {
        "metadata": {
            "source": "mock_generator",
            "n_samples": n_samples,
            "n_snps": n_snps,
            "seed": MOCK_SEED
        },
        "samples": pop_ids,
        "variants": [
            {
                "id": snp_ids[i],
                "position": int(positions[i]),
                "genotypes": genotype_matrix[:, i].tolist()
            }
            for i in range(n_snps)
        ]
    }
    return data

def generate_mock_environmental_data(n_samples: int = 100) -> Dict[str, Any]:
    """
    Generates mock environmental metadata.
    """
    np.random.seed(MOCK_SEED + 1)
    
    env_ids = generate_deterministic_env_ids(n_samples)
    
    data = {
        "metadata": {
            "source": "mock_generator",
            "n_samples": n_samples,
            "seed": MOCK_SEED + 1
        },
        "environments": [
            {
                "id": env_ids[i],
                "temperature_avg": float(np.random.normal(20, 5)),
                "precipitation": float(np.random.normal(1000, 200)),
                "elevation": int(np.random.normal(500, 300)),
                "soil_ph": float(np.random.normal(6.5, 0.5))
            }
            for i in range(n_samples)
        ]
    }
    return data

def generate_mock_compound_data(n_samples: int = 100, n_compounds: int = 10) -> Dict[str, Any]:
    """
    Generates mock defense compound profiles.
    """
    np.random.seed(MOCK_SEED + 2)
    
    pop_ids = generate_deterministic_population_ids(n_samples)
    cmp_ids = generate_deterministic_compound_ids(n_compounds)
    
    # Generate concentration data
    concentrations = np.random.lognormal(mean=2, sigma=1, size=(n_samples, n_compounds))
    
    data = {
        "metadata": {
            "source": "mock_generator",
            "n_samples": n_samples,
            "n_compounds": n_compounds,
            "seed": MOCK_SEED + 2
        },
        "compounds": cmp_ids,
        "profiles": [
            {
                "population_id": pop_ids[i],
                "concentrations": {
                    cmp_ids[j]: float(concentrations[i, j])
                    for j in range(n_compounds)
                }
            }
            for i in range(n_samples)
        ]
    }
    return data

def generate_all_mock_data() -> Dict[str, Any]:
    """
    Generates all three data types and returns them in a single structure.
    Useful for quick testing or when no real data is available.
    """
    return {
        "genomic": generate_mock_genomic_data(),
        "environmental": generate_mock_environmental_data(),
        "compound": generate_mock_compound_data()
    }
