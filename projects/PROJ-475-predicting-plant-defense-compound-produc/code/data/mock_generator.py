"""
Deterministic Mock Data Generator for CI and Testing.

Generates synthetic but consistent data to allow for reproducible tests
without requiring external API keys or network access.

NOTE: This module is intended for CI/CD and testing purposes only.
Production runs should use real data from verified sources.
"""
import json
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from utils.logging import get_module_logger

logger = get_module_logger(__name__)

# Seed for deterministic generation
MOCK_SEED = 42
np.random.seed(MOCK_SEED)

def generate_deterministic_population_ids(n: int = 10) -> List[str]:
    """Generate deterministic population IDs."""
    ids = []
    for i in range(n):
        # Create a deterministic hash based on index
        h = hashlib.md5(f"pop_{i}_{MOCK_SEED}".encode()).hexdigest()[:8]
        ids.append(f"POP_{h}")
    return ids

def generate_deterministic_env_ids(n: int = 10) -> List[str]:
    """Generate deterministic environment IDs."""
    ids = []
    for i in range(n):
        h = hashlib.md5(f"env_{i}_{MOCK_SEED}".encode()).hexdigest()[:8]
        ids.append(f"ENV_{h}")
    return ids

def generate_deterministic_compound_ids(n: int = 10) -> List[str]:
    """Generate deterministic compound IDs."""
    ids = []
    for i in range(n):
        h = hashlib.md5(f"cmp_{i}_{MOCK_SEED}".encode()).hexdigest()[:8]
        ids.append(f"CMP_{h}")
    return ids

def generate_mock_genomic_data(n_populations: int = 10) -> Dict[str, Any]:
    """
    Generate mock genomic data.
    
    Args:
        n_populations: Number of populations to generate data for.
        
    Returns:
        Dictionary containing mock genomic data.
    """
    logger.info(f"Generating mock genomic data for {n_populations} populations.")
    
    pop_ids = generate_deterministic_population_ids(n_populations)
    
    # Generate mock SNP data
    n_snps = 100
    snp_data = {}
    for i, pop_id in enumerate(pop_ids):
        # Generate random genotype frequencies (0, 1, 2)
        genotypes = np.random.randint(0, 3, size=n_snps)
        snp_data[pop_id] = {
            "genotypes": genotypes.tolist(),
            "snp_count": n_snps,
            "heterozygosity": float(np.mean(genotypes == 1)),
            "nucleotide_diversity": float(np.std(genotypes) * 0.5)
        }
    
    return {
        "metadata": {
            "source": "mock_generator",
            "n_populations": n_populations,
            "n_snps": n_snps,
            "seed": MOCK_SEED
        },
        "data": snp_data
    }

def generate_mock_environmental_data(n_populations: int = 10) -> Dict[str, Any]:
    """
    Generate mock environmental data.
    
    Args:
        n_populations: Number of populations to generate data for.
        
    Returns:
        Dictionary containing mock environmental data.
    """
    logger.info(f"Generating mock environmental data for {n_populations} populations.")
    
    pop_ids = generate_deterministic_population_ids(n_populations)
    env_ids = generate_deterministic_env_ids(n_populations)
    
    # Generate mock environmental variables
    env_data = {}
    for i, (pop_id, env_id) in enumerate(zip(pop_ids, env_ids)):
        # Generate realistic-looking environmental variables
        temp_mean = np.random.uniform(-5, 35)  # Mean annual temperature
        temp_range = np.random.uniform(5, 30)  # Temperature range
        precip = np.random.uniform(200, 3000)  # Annual precipitation
        humidity = np.random.uniform(20, 90)   # Relative humidity
        
        env_data[pop_id] = {
            "env_id": env_id,
            "temp_mean": round(temp_mean, 2),
            "temp_range": round(temp_range, 2),
            "precipitation": round(precip, 2),
            "humidity": round(humidity, 2),
            "elevation": int(np.random.uniform(0, 3000)),
            "latitude": round(np.random.uniform(-60, 60), 4),
            "longitude": round(np.random.uniform(-180, 180), 4)
        }
    
    return {
        "metadata": {
            "source": "mock_generator",
            "n_populations": n_populations,
            "seed": MOCK_SEED
        },
        "data": env_data
    }

def generate_mock_compound_data(n_populations: int = 10) -> Dict[str, Any]:
    """
    Generate mock compound data.
    
    Args:
        n_populations: Number of populations to generate data for.
        
    Returns:
        Dictionary containing mock compound data.
    """
    logger.info(f"Generating mock compound data for {n_populations} populations.")
    
    pop_ids = generate_deterministic_population_ids(n_populations)
    compound_ids = generate_deterministic_compound_ids(n_populations)
    
    # Generate mock compound concentrations
    compound_data = {}
    for i, (pop_id, cmp_id) in enumerate(zip(pop_ids, compound_ids)):
        # Generate realistic-looking compound concentrations
        phenolics = np.random.uniform(0.1, 10.0)
        terpenoids = np.random.uniform(0.05, 5.0)
        alkaloids = np.random.uniform(0.01, 2.0)
        flavonoids = np.random.uniform(0.1, 8.0)
        
        compound_data[pop_id] = {
            "compound_id": cmp_id,
            "phenolics": round(phenolics, 4),
            "terpenoids": round(terpenoids, 4),
            "alkaloids": round(alkaloids, 4),
            "flavonoids": round(flavonoids, 4),
            "total_defense": round(phenolics + terpenoids + alkaloids + flavonoids, 4)
        }
    
    return {
        "metadata": {
            "source": "mock_generator",
            "n_populations": n_populations,
            "seed": MOCK_SEED
        },
        "data": compound_data
    }

def generate_all_mock_data(n_populations: int = 10) -> Dict[str, Any]:
    """
    Generate all mock data types.
    
    Args:
        n_populations: Number of populations to generate data for.
        
    Returns:
        Dictionary containing all mock data.
    """
    logger.info("Generating all mock data.")
    
    return {
        "genomic": generate_mock_genomic_data(n_populations),
        "environmental": generate_mock_environmental_data(n_populations),
        "compound": generate_mock_compound_data(n_populations)
    }

def main() -> int:
    """
    Main entry point for the mock generator script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    configure_root_logger()
    logger.info("Starting mock data generation.")
    
    try:
        # Generate all mock data
        data = generate_all_mock_data(n_populations=10)
        
        # Save to files
        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "genomic_vcf.json", 'w') as f:
            json.dump(data["genomic"], f, indent=2)
        
        with open(output_dir / "env_data.json", 'w') as f:
            json.dump(data["environmental"], f, indent=2)
        
        with open(output_dir / "compound_data.json", 'w') as f:
            json.dump(data["compound"], f, indent=2)
        
        logger.info("Mock data generation completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Mock data generation failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    from utils.logging import configure_root_logger
    configure_root_logger()
    sys.exit(main())
