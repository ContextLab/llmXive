"""
Synthetic Data Generator for Plant VOC Studies.

This module generates a canonical synthetic dataset for testing and fallback
when real data is unavailable. It ensures the generated data adheres to the
schema defined in specs/001-predict-voc-profiles/contracts/dataset.schema.yaml.

Outputs:
    - data/raw/synthetic_arabidopsis_v1.csv
"""
import os
import random
import hashlib
import json
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Ensure directory exists
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Constants
RANDOM_SEED = 42
NUM_SAMPLES = 100  # Generate enough to pass the >= 50 threshold
GENE_COUNT = 20    # Number of genomic features
VOC_COUNT = 10     # Number of VOC features

def set_seed(seed: int = RANDOM_SEED) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def generate_sample_id(index: int) -> str:
    """Generates a unique sample ID."""
    return f"AT_STRESS_{index:04d}"

def generate_environmental_features() -> Dict[str, Any]:
    """Generates random environmental features."""
    return {
        "temperature": round(random.uniform(20.0, 35.0), 2),
        "light_intensity": round(random.uniform(100.0, 1000.0), 2),
        "co2_level": round(random.uniform(300.0, 600.0), 2),
        "humidity": round(random.uniform(40.0, 90.0), 2),
        "stress_type": random.choice(["drought", "heat", "cold", "salt"])
    }

def generate_genomic_features() -> Dict[str, float]:
    """Generates random genomic features (TPM values)."""
    features = {}
    for i in range(GENE_COUNT):
        gene_name = f"Gene_{i+1:03d}"
        # Simulate TPM distribution (log-normal-ish)
        value = max(0, np.random.lognormal(mean=2, sigma=1))
        features[gene_name] = round(value, 4)
    return features

def generate_voc_profile() -> Dict[str, float]:
    """Generates random VOC profiles."""
    vocs = {}
    voc_names = ["limonene", "pinene", "linalool", "geraniol", "nerolidol", 
                 "caryophyllene", "farnesene", "myrcene", "ocimene", "terpineol"]
    for name in voc_names:
        # Simulate concentration (ppb)
        value = max(0, np.random.lognormal(mean=1, sigma=0.8))
        vocs[name] = round(value, 4)
    return vocs

def generate_synthetic_dataset(output_path: Optional[str] = None) -> str:
    """
    Generates the full synthetic dataset and saves it to CSV.
    
    Args:
        output_path: Path to save the CSV. Defaults to data/raw/synthetic_arabidopsis_v1.csv.
        
    Returns:
        Path to the generated file.
    """
    if output_path is None:
        output_path = str(DATA_RAW_DIR / "synthetic_arabidopsis_v1.csv")
    
    set_seed(RANDOM_SEED)
    
    rows = []
    for i in range(NUM_SAMPLES):
        sample_id = generate_sample_id(i)
        env_data = generate_environmental_features()
        genomic_data = generate_genomic_features()
        voc_data = generate_voc_profile()
        
        # Flatten into a single row
        row = {
            "sample_id": sample_id,
            **env_data,
            **genomic_data,
            **voc_data
        }
        rows.append(row)
    
    # Write to CSV
    fieldnames = list(rows[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Synthetic dataset generated: {output_path} ({len(rows)} samples)")
    return output_path

def compute_file_hash(file_path: str) -> str:
    """Computes SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_against_schema(file_path: str) -> bool:
    """
    Validates the generated CSV against the expected schema.
    Checks for required columns and basic data types.
    """
    required_cols = ["sample_id", "temperature", "light_intensity", "co2_level"]
    try:
        df = pd.read_csv(file_path)
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            print(f"Schema validation failed: Missing columns {missing}")
            return False
        
        # Check numeric types for environmental features
        for col in ["temperature", "light_intensity", "co2_level"]:
            if not pd.api.types.is_numeric_dtype(df[col]):
                print(f"Schema validation failed: {col} is not numeric")
                return False
        
        print("Schema validation passed.")
        return True
    except Exception as e:
        print(f"Schema validation error: {e}")
        return False

def main():
    """Main entry point for synthetic data generation."""
    output_file = str(DATA_RAW_DIR / "synthetic_arabidopsis_v1.csv")
    generate_synthetic_dataset(output_file)
    
    if validate_against_schema(output_file):
        file_hash = compute_file_hash(output_file)
        print(f"File hash: {file_hash}")
    else:
        print("Validation failed. File may be incomplete.")

if __name__ == "__main__":
    main()
