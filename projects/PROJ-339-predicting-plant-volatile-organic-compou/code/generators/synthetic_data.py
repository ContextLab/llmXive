"""
Synthetic Data Generator for Arabidopsis thaliana VOC Study.

This module generates a canonical synthetic dataset that matches the schema
defined in specs/001-predict-voc-profiles/contracts/dataset.schema.yaml.

It is used as a fallback when real data ingestion fails or for development
purposes. The output is checksummed to ensure reproducibility.
"""
import os
import random
import hashlib
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import config and hashing utilities from existing API surface
try:
    from utils.config import get_config
    from utils.hashing import compute_file_hash
except ImportError:
    # Fallback for direct execution context if imports fail
    def get_config():
        return {
            "DATA_PATH": str(Path(__file__).parent.parent.parent / "data"),
            "RANDOM_SEED": 42
        }
    def compute_file_hash(filepath: str) -> str:
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


# Constants for synthetic generation
RANDOM_SEED = 42
NUM_SAMPLES = 100  # Ensure >= 50 as per task requirements
SPECIES = "Arabidopsis thaliana"

# Gene families and pathways for realistic synthetic data
TPS_FAMILIES = ["TPSa", "TPSb", "TPSc", "TPSd", "TPSe", "TPSf", "TPSg"]
VOC_COMPOUNDS = [
    "Limonene", "Pinene", "Myrcene", "Ocimene", "Linalool", 
    "Geraniol", "Nerolidol", "Farnesene", "Sesquiterpene"
]
STRESS_TYPES = ["Drought", "Heat", "Cold", "Pathogen", "Herbivory"]

# Environmental ranges (realistic units)
TEMP_RANGE = (15.0, 35.0)  # Celsius
LIGHT_RANGE = (100.0, 1000.0)  # µmol/m²/s
CO2_RANGE = (350.0, 800.0)  # ppm
HUMIDITY_RANGE = (30.0, 90.0)  # %

def _set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def _generate_sample_id(index: int) -> str:
    """Generate a unique sample ID."""
    return f"AT_Synth_{index:04d}"

def _generate_genomic_features() -> Dict[str, float]:
    """
    Generate synthetic genomic feature values (TPM normalized).
    Values are log-normal distributed to mimic RNA-seq counts.
    """
    features = {}
    for family in TPS_FAMILIES:
        # Some families are more active, some less
        base_mean = random.uniform(10.0, 500.0)
        # Add noise
        value = max(0.1, random.gauss(base_mean, base_mean * 0.3))
        features[f"{family}_TPM"] = round(value, 4)
    
    # Add some non-TPS genes for dimensionality
    for i in range(10):
        features[f"Gene_{i+1}_TPM"] = round(random.uniform(0.5, 100.0), 4)
        
    return features

def _generate_environmental_features() -> Dict[str, float]:
    """Generate synthetic environmental metadata."""
    return {
        "temperature": round(random.uniform(*TEMP_RANGE), 2),
        "light_intensity": round(random.uniform(*LIGHT_RANGE), 2),
        "co2_level": round(random.uniform(*CO2_RANGE), 2),
        "humidity": round(random.uniform(*HUMIDITY_RANGE), 2)
    }

def _generate_voc_profile() -> Dict[str, float]:
    """Generate synthetic VOC emission rates (ng/g/h)."""
    profile = {}
    for compound in VOC_COMPOUNDS:
        # Emission rates vary widely
        value = max(0.0, random.lognormvariate(0, 1.5) * 10)
        profile[f"{compound}_rate"] = round(value, 4)
    return profile

def _generate_metadata(index: int) -> Dict[str, Any]:
    """Generate sample metadata."""
    return {
        "sample_id": _generate_sample_id(index),
        "species": SPECIES,
        "stress_type": random.choice(STRESS_TYPES),
        "replicate": (index % 3) + 1,  # Ensure replicates exist
        "treatment_day": random.randint(1, 14)
    }

def generate_synthetic_dataset(
    output_path: str,
    num_samples: int = NUM_SAMPLES,
    seed: int = RANDOM_SEED
) -> Dict[str, Any]:
    """
    Generate a complete synthetic dataset matching the project schema.
    
    Args:
        output_path: Path to save the CSV file.
        num_samples: Number of samples to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing generation metadata and checksum.
    """
    _set_seed(seed)
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Define column headers based on schema (Sample + Genomic + Environmental + VOC)
    # We will flatten the nested dicts for CSV storage
    base_columns = ["sample_id", "species", "stress_type", "replicate", "treatment_day"]
    genomic_columns = [f"{f}_TPM" for f in TPS_FAMILIES] + [f"Gene_{i+1}_TPM" for i in range(10)]
    env_columns = ["temperature", "light_intensity", "co2_level", "humidity"]
    voc_columns = [f"{c}_rate" for c in VOC_COMPOUNDS]
    
    all_columns = base_columns + genomic_columns + env_columns + voc_columns
    
    rows = []
    for i in range(num_samples):
        metadata = _generate_metadata(i)
        genomic = _generate_genomic_features()
        env = _generate_environmental_features()
        voc = _generate_voc_profile()
        
        # Flatten and combine
        row = {
            "sample_id": metadata["sample_id"],
            "species": metadata["species"],
            "stress_type": metadata["stress_type"],
            "replicate": metadata["replicate"],
            "treatment_day": metadata["treatment_day"],
            **genomic,
            **env,
            **voc
        }
        rows.append(row)
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_columns)
        writer.writeheader()
        writer.writerows(rows)
    
    # Compute checksum
    checksum = compute_file_hash(str(output_file))
    
    return {
        "output_path": str(output_file),
        "num_samples": num_samples,
        "seed": seed,
        "checksum": checksum,
        "columns": all_columns
    }
    
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
    
    return manifest

def main():
    """Main entry point for synthetic data generation."""
    config = get_config()
    data_path = Path(config.get("DATA_PATH", "data"))
    output_file = data_path / "raw" / "synthetic_arabidopsis_v1.csv"
    
    print(f"Generating synthetic dataset to: {output_file}")
    result = generate_synthetic_dataset(str(output_file))
    
    print(f"Generated {result['num_samples']} samples.")
    print(f"Checksum: {result['checksum']}")
    print(f"Columns: {len(result['columns'])}")
    
    # Save generation metadata
    meta_path = output_file.parent / "synthetic_metadata.json"
    with open(meta_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Metadata saved to: {meta_path}")

if __name__ == "__main__":
    main()