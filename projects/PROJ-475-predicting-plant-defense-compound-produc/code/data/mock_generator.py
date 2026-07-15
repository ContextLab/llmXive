"""
Mock Data Generator for CI and Testing.

Generates deterministic mock genomic, environmental, and compound data
to allow pipeline execution without external API keys or network access.
"""
import json
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Seed for determinism
MOCK_SEED = 42

def _deterministic_hash(seed_str: str, length: int = 8) -> str:
    """Generate a deterministic string from a seed."""
    return hashlib.sha256(f"{MOCK_SEED}_{seed_str}".encode()).hexdigest()[:length]

def generate_deterministic_population_ids(n: int) -> List[str]:
    """Generate deterministic population IDs."""
    return [f"POP-{_deterministic_hash(str(i))}" for i in range(n)]

def generate_deterministic_env_ids(n: int) -> List[str]:
    """Generate deterministic environmental IDs."""
    return [f"ENV-{_deterministic_hash(str(i))}" for i in range(n)]

def generate_deterministic_compound_ids(n: int) -> List[str]:
    """Generate deterministic compound IDs."""
    return [f"CMP-{_deterministic_hash(str(i))}" for i in range(n)]

def generate_mock_genomic_data(n_populations: int = 10, n_snps: int = 100) -> List[Dict[str, Any]]:
    """
    Generate deterministic mock genomic data.
    
    Returns a list of dictionaries representing SNP genotypes per population.
    Structure: [{"population_id": str, "snp_id": str, "genotype": float}, ...]
    """
    np.random.seed(MOCK_SEED)
    pop_ids = generate_deterministic_population_ids(n_populations)
    data = []
    
    for i, pop_id in enumerate(pop_ids):
        for j in range(n_snps):
            snp_id = f"SNP-{_deterministic_hash(f'{i}_{j}')}"
            # Simulate genotype frequencies (0, 1, 2 alleles)
            genotype = np.random.choice([0, 1, 2], p=[0.4, 0.4, 0.2])
            # Add small missingness (5%)
            if np.random.random() < 0.05:
                genotype = None
            data.append({
                "population_id": pop_id,
                "snp_id": snp_id,
                "genotype": float(genotype) if genotype is not None else None
            })
    return data

def generate_mock_environmental_data(n_populations: int = 10) -> List[Dict[str, Any]]:
    """
    Generate deterministic mock environmental data.
    
    Returns a list of dictionaries with environmental variables per population.
    Structure: [{"population_id": str, "env_id": str, "temp_mean": float, "precip_mean": float, ...}]
    """
    np.random.seed(MOCK_SEED + 1)
    pop_ids = generate_deterministic_population_ids(n_populations)
    data = []
    
    for i, pop_id in enumerate(pop_ids):
        env_id = generate_deterministic_env_ids(1)[0]
        data.append({
            "population_id": pop_id,
            "env_id": env_id,
            "temp_mean": float(np.random.uniform(10, 30)),
            "precip_mean": float(np.random.uniform(500, 2000)),
            "altitude": float(np.random.uniform(0, 2000)),
            "source_study": f"STUDY-{_deterministic_hash(str(i))}"
        })
    return data

def generate_mock_compound_data(n_populations: int = 10) -> List[Dict[str, Any]]:
    """
    Generate deterministic mock defense compound profiles.
    
    Returns a list of dictionaries with compound concentrations per population.
    Structure: [{"population_id": str, "compound_id": str, "concentration": float, ...}]
    """
    np.random.seed(MOCK_SEED + 2)
    pop_ids = generate_deterministic_population_ids(n_populations)
    compounds = ["alkaloid_A", "terpenoid_B", "phenolic_C", "glucosinolate_D"]
    data = []
    
    for i, pop_id in enumerate(pop_ids):
        for compound in compounds:
            cmp_id = generate_deterministic_compound_ids(1)[0]
            # Concentration in mg/g
            concentration = float(np.random.uniform(0.1, 10.0))
            # Add small missingness (5%)
            if np.random.random() < 0.05:
                concentration = None
            data.append({
                "population_id": pop_id,
                "compound_id": cmp_id,
                "compound_name": compound,
                "concentration": concentration
            })
    return data

def generate_all_mock_data(n_populations: int = 10) -> Dict[str, Any]:
    """
    Generate all three data modalities with consistent population IDs.
    
    Returns a dictionary containing:
    - genomic: List[Dict]
    - environmental: List[Dict]
    - compounds: List[Dict]
    """
    return {
        "genomic": generate_mock_genomic_data(n_populations),
        "environmental": generate_mock_environmental_data(n_populations),
        "compounds": generate_mock_compound_data(n_populations)
    }

def save_mock_data(data: Dict[str, Any], output_dir: Path = Path("data/raw")) -> None:
    """Save generated mock data to JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "genomic_vcf.json", 'w') as f:
        json.dump(data["genomic"], f, indent=2)
    with open(output_dir / "env_data.json", 'w') as f:
        json.dump(data["environmental"], f, indent=2)
    with open(output_dir / "compound_data.json", 'w') as f:
        json.dump(data["compounds"], f, indent=2)

def main():
    """Entry point for generating mock data."""
    import logging
    from utils.logging import configure_root_logger
    configure_root_logger = logging.getLogger()
    configure_root_logger.setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("Generating mock data...")
    data = generate_all_mock_data()
    save_mock_data(data)
    logger.info("Mock data generation complete.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
