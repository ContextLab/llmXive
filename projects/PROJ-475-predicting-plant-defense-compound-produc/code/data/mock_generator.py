"""
Mock data generator for CI runs.

Generates deterministic mock genomic, environmental, and compound data
to satisfy the 'no manual key injection' constraint and remove the need
for external API keys during testing.
"""
import json
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from existing project utilities
from utils.logging import get_module_logger
from utils.io import compute_checksum

logger = get_module_logger(__name__)

# Seed for deterministic generation
MOCK_SEED = 42
np.random.seed(MOCK_SEED)

# Configuration for mock data dimensions
NUM_POPULATIONS = 50
NUM_ENV_SITES = 50
NUM_COMPOUNDS = 20
NUM_SNPS = 1000  # Reduced for CI speed

def _generate_population_ids(n: int) -> List[str]:
    """Generate deterministic population IDs."""
    return [f"POP_{i:03d}" for i in range(n)]

def _generate_env_ids(n: int) -> List[str]:
    """Generate deterministic environmental site IDs."""
    return [f"ENV_{i:03d}" for i in range(n)]

def _generate_compound_ids(n: int) -> List[str]:
    """Generate deterministic compound IDs."""
    compounds = [
        "salicylic_acid", "jasmonic_acid", "abscisic_acid", 
        "ethylene", "brassinosteroid", "auxin", "gibberellin",
        "flavonoid_A", "flavonoid_B", "alkaloid_X", "terpene_Y",
        "phenol_Z", "tannin_A", "lignan_B", "coumarin_C",
        "glucosinolate_D", "cyanogenic_E", "saponin_F", "lectin_G", "protease_H"
    ]
    return compounds[:n]

def _generate_genomic_data(pop_ids: List[str], num_snps: int) -> Dict[str, Any]:
    """
    Generate mock genomic VCF-like data.
    
    Returns a dictionary structure compatible with VCF JSON representation.
    """
    logger.info(f"Generating genomic data for {len(pop_ids)} populations with {num_snps} SNPs")
    
    # Generate random genotypes (0, 1, 2 representing 0, 1, 2 alternate alleles)
    # Ploidy assumed 2 (diploid)
    genotypes = np.random.choice([0, 1, 2], size=(len(pop_ids), num_snps), p=[0.7, 0.2, 0.1])
    
    # Generate variant metadata
    variants = []
    for i in range(num_snps):
        pos = 1000 + i * 500  # Deterministic positions
        variants.append({
            "chrom": "chr1",
            "pos": pos,
            "id": f"SNP_{i:05d}",
            "ref": "A",
            "alt": "T",
            "qual": 99.0,
            "filter": "PASS",
            "info": {"AF": round(np.random.uniform(0.05, 0.5), 3)}
        })
    
    # Format as list of population records
    data = []
    for idx, pop_id in enumerate(pop_ids):
        record = {
            "population_id": pop_id,
            "genotypes": genotypes[idx].tolist(),
            "variant_ids": [v["id"] for v in variants]
        }
        data.append(record)
    
    return {
        "metadata": {
            "source": "mock_generator",
            "seed": MOCK_SEED,
            "num_populations": len(pop_ids),
            "num_variants": num_snps
        },
        "variants": variants,
        "samples": data
    }

def _generate_environmental_data(env_ids: List[str]) -> Dict[str, Any]:
    """
    Generate mock environmental metadata.
    
    Simulates WorldClim/GBIF style data with temperature, precipitation, etc.
    """
    logger.info(f"Generating environmental data for {len(env_ids)} sites")
    
    data = []
    for idx, env_id in enumerate(env_ids):
        # Deterministic but varied environmental conditions
        base_temp = 20 + (idx % 10) * 2 - 10  # Range 10-30
        base_precip = 500 + (idx % 15) * 50   # Range 500-1200
        
        record = {
            "env_id": env_id,
            "latitude": round(-30 + (idx % 60) * 1.5, 4),
            "longitude": round(120 + (idx % 40) * 2.0, 4),
            "annual_mean_temp": round(base_temp + np.random.normal(0, 1), 2),
            "temp_seasonality": round(np.random.uniform(10, 30), 2),
            "annual_precip": round(base_precip + np.random.normal(0, 50), 2),
            "precip_seasonality": round(np.random.uniform(50, 150), 2),
            "soil_ph": round(np.random.uniform(4.5, 8.0), 2),
            "elevation": int(100 + (idx % 20) * 100)
        }
        data.append(record)
    
    return {
        "metadata": {
            "source": "mock_generator",
            "seed": MOCK_SEED,
            "num_sites": len(env_ids)
        },
        "environmental_data": data
    }

def _generate_compound_data(pop_ids: List[str], compound_ids: List[str]) -> Dict[str, Any]:
    """
    Generate mock defense compound profiles.
    
    Simulates ChemBank/PhenolExplorer style concentration data.
    """
    logger.info(f"Generating compound data for {len(pop_ids)} populations and {len(compound_ids)} compounds")
    
    data = []
    for pop_idx, pop_id in enumerate(pop_ids):
        for comp_idx, comp_id in enumerate(compound_ids):
            # Create some correlation structure for realism
            # Some compounds vary by population, others are relatively constant
            base_conc = 10 + (pop_idx % 5) * 5  # Population effect
            compound_factor = 1.0 + (comp_idx % 3) * 0.5  # Compound effect
            
            concentration = base_conc * compound_factor * np.random.uniform(0.8, 1.2)
            detection = concentration > 0.5
            
            record = {
                "population_id": pop_id,
                "compound_id": comp_id,
                "concentration_umol_g": round(concentration, 4) if detection else 0.0,
                "detection_limit": 0.5,
                "assay_method": "HPLC",
                "unit": "umol/g_dw"
            }
            data.append(record)
    
    return {
        "metadata": {
            "source": "mock_generator",
            "seed": MOCK_SEED,
            "num_populations": len(pop_ids),
            "num_compounds": len(compound_ids)
        },
        "compound_profiles": data
    }

def generate_all_mock_data(output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Generate all mock datasets and save to disk.
    
    Args:
        output_dir: Directory to save files. Defaults to 'data/raw'.
        
    Returns:
        Dictionary mapping dataset type to file path.
    """
    if output_dir is None:
        output_dir = "data/raw"
    
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Generate IDs
    pop_ids = _generate_population_ids(NUM_POPULATIONS)
    env_ids = _generate_env_ids(NUM_ENV_SITES)
    compound_ids = _generate_compound_ids(NUM_COMPOUNDS)
    
    # Generate datasets
    genomic_data = _generate_genomic_data(pop_ids, NUM_SNPS)
    env_data = _generate_environmental_data(env_ids)
    compound_data = _generate_compound_data(pop_ids, compound_ids)
    
    # Save files
    file_paths = {}
    
    # Genomic data
    genomic_file = out_path / "genomic_vcf.json"
    with open(genomic_file, "w") as f:
        json.dump(genomic_data, f, indent=2)
    file_paths["genomic"] = str(genomic_file)
    logger.info(f"Saved genomic data to {genomic_file}")
    
    # Environmental data
    env_file = out_path / "env_data.json"
    with open(env_file, "w") as f:
        json.dump(env_data, f, indent=2)
    file_paths["environmental"] = str(env_file)
    logger.info(f"Saved environmental data to {env_file}")
    
    # Compound data
    compound_file = out_path / "compound_data.json"
    with open(compound_file, "w") as f:
        json.dump(compound_data, f, indent=2)
    file_paths["compound"] = str(compound_file)
    logger.info(f"Saved compound data to {compound_file}")
    
    # Generate checksums
    checksums = {}
    for key, path in file_paths.items():
        checksums[key] = compute_checksum(path)
    
    # Save manifest
    manifest = {
        "generated_at": "2024-01-01T00:00:00Z", # Fixed for determinism
        "seed": MOCK_SEED,
        "files": file_paths,
        "checksums": checksums
    }
    manifest_file = out_path / "mock_manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"All mock data generated successfully. Manifest: {manifest_file}")
    return file_paths

if __name__ == "__main__":
    logger.info("Starting mock data generation for CI...")
    generate_all_mock_data()
    logger.info("Mock data generation complete.")
