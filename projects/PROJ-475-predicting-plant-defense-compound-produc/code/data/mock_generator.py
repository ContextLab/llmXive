"""
Deterministic Mock Data Generator for CI and Testing.

Generates synthetic but consistent data to avoid network calls during CI.
This module is invoked ONLY when verified URLs are missing or invalid.
"""

import json
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Seed for reproducibility
SEED = 42
np.random.seed(SEED)

def _get_deterministic_hash(seed_str: str) -> int:
    """Generate a deterministic integer from a string."""
    return int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)

def generate_deterministic_population_ids(n: int = 10) -> List[str]:
    """Generate deterministic population IDs."""
    ids = []
    for i in range(n):
        ids.append(f"POP_{i:04d}")
    return ids

def generate_deterministic_env_ids(n: int = 10) -> List[str]:
    """Generate deterministic environment IDs."""
    ids = []
    for i in range(n):
        ids.append(f"ENV_{i:04d}")
    return ids

def generate_deterministic_compound_ids(n: int = 10) -> List[str]:
    """Generate deterministic compound IDs."""
    ids = []
    for i in range(n):
        ids.append(f"CMP_{i:04d}")
    return ids

def generate_mock_genomic_data(n_populations: int = 10, n_variants: int = 100) -> Dict[str, Any]:
    """
    Generate mock genomic VCF data in JSON format.

    Args:
        n_populations: Number of populations.
        n_variants: Number of variants per population.

    Returns:
        Dictionary containing genomic data.
    """
    population_ids = generate_deterministic_population_ids(n_populations)
    variants = []

    for pop_id in population_ids:
        pop_variants = []
        for i in range(n_variants):
            var_id = f"VAR_{pop_id}_{i:03d}"
            # Deterministic genotype values (0, 1, 2)
            genotype = _get_deterministic_hash(f"{pop_id}_{var_id}") % 3
            pop_variants.append({
                "variant_id": var_id,
                "chromosome": 1 + (i % 22),
                "position": 1000 + i * 100,
                "ref_allele": "A",
                "alt_allele": "T",
                "genotype": genotype
            })
        variants.append({
            "population_id": pop_id,
            "variants": pop_variants
        })

    return {
        "metadata": {
            "source": "mock_generator",
            "seed": SEED,
            "n_populations": n_populations,
            "n_variants": n_variants
        },
        "data": variants
    }

def generate_mock_environmental_data(n_populations: int = 10) -> List[Dict[str, Any]]:
    """
    Generate mock environmental data.

    Args:
        n_populations: Number of populations.

    Returns:
        List of environmental records.
    """
    population_ids = generate_deterministic_population_ids(n_populations)
    records = []

    for i, pop_id in enumerate(population_ids):
        # Deterministic values based on index
        lat = 30.0 + (i % 5) * 10.0
        lon = -120.0 + (i % 5) * 20.0
        temp = 15.0 + (i % 3) * 5.0
        precip = 500.0 + (i % 4) * 200.0
        ph = 6.0 + (i % 3) * 0.5

        records.append({
            "population_id": pop_id,
            "env_id": f"ENV_{i:04d}",
            "lat": lat,
            "lon": lon,
            "temp": temp,
            "precip": precip,
            "ph": ph
        })

    return records

def generate_mock_compound_data(n_populations: int = 10, n_compounds: int = 5) -> List[Dict[str, Any]]:
    """
    Generate mock defense compound data.

    Args:
        n_populations: Number of populations.
        n_compounds: Number of compounds per population.

    Returns:
        List of compound records.
    """
    population_ids = generate_deterministic_population_ids(n_populations)
    compound_names = ["Alkaloid_A", "Terpenoid_B", "Phenolic_C", "Flavonoid_D", "Glycoside_E"]
    records = []

    for i, pop_id in enumerate(population_ids):
        for j in range(min(n_compounds, len(compound_names))):
            # Deterministic concentration based on hash
            base_conc = 10.0 + (_get_deterministic_hash(f"{pop_id}_{compound_names[j]}") % 100)
            concentration = base_conc + (i * 0.1) + (j * 0.05)

            records.append({
                "population_id": pop_id,
                "compound_name": compound_names[j],
                "concentration": round(concentration, 2),
                "source_study": f"STUDY_{(i % 3) + 1}"
            })

    return records

def generate_all_mock_data() -> Dict[str, Any]:
    """
    Generate all mock data types.

    Returns:
        Dictionary containing all mock data.
    """
    return {
        "genomic": generate_mock_genomic_data(),
        "environmental": generate_mock_environmental_data(),
        "compounds": generate_mock_compound_data()
    }

def main() -> int:
    """Main entry point for the mock generator script."""
    print("Generating all mock data...")
    data = generate_all_mock_data()
    print(json.dumps(data, indent=2))
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
