"""
Synthetic Data Generator for Arabidopsis thaliana VOC Studies.

This module provides the canonical source for mock data used in local unit testing
and development validation ONLY. It MUST NOT be used as a fallback for real data
ingestion in the production pipeline.

The generated data follows the schema defined in specs/001-predict-voc-profiles/contracts/dataset.schema.yaml
and includes checksums for verification.
"""
import os
import random
import hashlib
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = DATA_RAW_DIR / "synthetic_arabidopsis_v1.csv"
MANIFEST_FILE = DATA_RAW_DIR / "synthetic_manifest.json"

# Schema definitions
TREATMENT_OPTIONS = ["control", "drought", "heat", "cold", "herbivory", "pathogen"]
VOC_CATEGORIES = ["monoterpenes", "sesquiterpenes", "green_leaf_volatiles", "benzenoids"]

def generate_synthetic_arabidopsis(n_samples: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic Arabidopsis thaliana dataset for testing.

    Args:
        n_samples: Number of samples to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with synthetic data matching the project schema.

    Raises:
        ValueError: If n_samples is non-positive.
    """
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")

    random.seed(seed)
    np.random.seed(seed)

    data = {
        "sample_id": [f"ATH_{i:04d}" for i in range(1, n_samples + 1)],
        "temperature": np.random.normal(loc=22.0, scale=3.0, size=n_samples).round(2),
        "light_intensity": np.random.uniform(low=100, high=1000, size=n_samples).round(2),
        "co2_level": np.random.normal(loc=400, scale=50, size=n_samples).round(2),
        "treatment": [random.choice(TREATMENT_OPTIONS) for _ in range(n_samples)],
        "voc_concentration": []
    }

    # Generate VOC concentration based on environmental factors
    # This creates a realistic correlation structure
    for i in range(n_samples):
        temp = data["temperature"][i]
        light = data["light_intensity"][i]
        co2 = data["co2_level"][i]
        treatment = data["treatment"][i]

        # Base concentration
        base = 10.0

        # Temperature effect (optimal around 25C)
        temp_effect = -0.5 * (temp - 25.0) ** 2 + 20.0

        # Light effect (linear increase)
        light_effect = 0.01 * light

        # CO2 effect (slight negative correlation)
        co2_effect = -0.02 * (co2 - 400)

        # Treatment effect
        treatment_effects = {
            "control": 0,
            "drought": 15,
            "heat": 25,
            "cold": -5,
            "herbivory": 30,
            "pathogen": 10
        }
        treatment_effect = treatment_effects.get(treatment, 0)

        # Add noise
        noise = np.random.normal(0, 5)

        conc = base + temp_effect + light_effect + co2_effect + treatment_effect + noise
        data["voc_concentration"].append(round(max(0, conc), 2))

    # Generate gene expression data (wide format for simplicity)
    # Simulate 20 key genes related to terpene synthesis
    gene_prefixes = ["TPS", "DXS", "HMGR", "GGPPS", "FPS"]
    gene_suffixes = ["a1", "a2", "b1", "b2", "c1", "c2", "d1", "d2"]
    
    gene_columns = []
    for prefix in gene_prefixes:
        for suffix in gene_suffixes:
            gene_columns.append(f"{prefix}_{suffix}")
    
    # Limit to 20 genes for manageability
    selected_genes = gene_columns[:20]
    
    for gene in selected_genes:
        # Gene expression follows log-normal distribution
        data[gene] = np.random.lognormal(mean=2.0, sigma=1.0, size=n_samples).round(4)
    
    # Add some missing values to test imputation (but keep it realistic)
    # ~5% missingness in gene expression
    for gene in selected_genes:
        missing_indices = np.random.choice(n_samples, size=int(n_samples * 0.05), replace=False)
        for idx in missing_indices:
            data[gene][idx] = np.nan

    df = pd.DataFrame(data)
    
    # Ensure sample_id is string
    df["sample_id"] = df["sample_id"].astype(str)
    
    # Ensure treatment is categorical
    df["treatment"] = df["treatment"].astype("category")
    
    return df

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_manifest(file_path: Path, df: pd.DataFrame, n_samples: int, seed: int) -> Dict[str, Any]:
    """Save a manifest with metadata and checksums."""
    file_hash = compute_file_hash(file_path)
    
    manifest = {
        "file_path": str(file_path),
        "file_hash": file_hash,
        "n_samples": n_samples,
        "seed": seed,
        "columns": list(df.columns),
        "generated_at": pd.Timestamp.now().isoformat(),
        "description": "Synthetic Arabidopsis thaliana VOC dataset for local testing only",
        "usage_warning": "This data is synthetic and MUST NOT be used as a fallback for real data ingestion"
    }
    
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
    
    return manifest

def main():
    """Main entry point for synthetic data generation."""
    # Ensure output directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating synthetic Arabidopsis dataset...")
    print(f"Output path: {OUTPUT_FILE}")
    
    # Generate data
    df = generate_synthetic_arabidopsis(n_samples=100, seed=42)
    
    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    
    # Save manifest
    manifest = save_manifest(OUTPUT_FILE, df, n_samples=100, seed=42)
    
    print(f"Successfully generated {len(df)} samples.")
    print(f"Columns: {list(df.columns)}")
    print(f"File hash: {manifest['file_hash']}")
    print(f"Manifest saved to: {MANIFEST_FILE}")
    
    # Verify file exists and is readable
    if not OUTPUT_FILE.exists():
        raise RuntimeError(f"Failed to create output file: {OUTPUT_FILE}")
    
    # Verify content
    loaded_df = pd.read_csv(OUTPUT_FILE)
    assert len(loaded_df) == 100, "Sample count mismatch"
    assert "sample_id" in loaded_df.columns, "Missing sample_id column"
    assert "voc_concentration" in loaded_df.columns, "Missing voc_concentration column"
    
    print("Verification passed.")
    return OUTPUT_FILE

if __name__ == "__main__":
    main()