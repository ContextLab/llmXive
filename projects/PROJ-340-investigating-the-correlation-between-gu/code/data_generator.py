import os
import sys
import json
import random
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Constants
CONFIG_DIR = Path("data/config")
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
METADATA_DIR = DATA_DIR / "metadata"
SCHEMAS_DIR = Path("specs/001-gut-microbiome-sleep-architecture/contracts")

def set_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def calculate_script_checksum(script_path: Path) -> str:
    """Calculate SHA256 checksum of a script file."""
    sha256_hash = hashlib.sha256()
    with open(script_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_real_data_flag_and_fail(mode: str):
    """Check if real data is requested and fail if synthetic mode is active."""
    if mode == 'real':
        # In a real scenario, this would check for actual data availability
        # For now, we simulate the check
        raise NotImplementedError("Real data mode is not yet implemented. Please use --mode synthetic for validation.")

def load_required_variables() -> tuple:
    """Load required variables from config."""
    config_path = CONFIG_DIR / "required_variables.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('predictors', []), config.get('outcomes', [])

def generate_metagenomic_counts(n_subjects: int, taxa: list, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic metagenomic count data.
    Note: This is for pipeline validation only, NOT for biological inference.
    """
    set_seeds(seed)
    
    # Generate counts with realistic zero-inflation
    data = {}
    for taxon in taxa:
        # Generate counts with some zeros (zero-inflation)
        counts = np.random.negative_binomial(n=5, p=0.3, size=n_subjects)
        # Add ~30% zeros to simulate zero-inflation
        zero_indices = np.random.choice(n_subjects, size=int(n_subjects * 0.3), replace=False)
        counts[zero_indices] = 0
        data[taxon] = counts
    
    df = pd.DataFrame(data)
    df['subject_id'] = range(1, n_subjects + 1)
    return df

def generate_sleep_metrics(n_subjects: int, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic sleep architecture metrics.
    Note: This is for pipeline validation only, NOT for biological inference.
    """
    set_seeds(seed)
    
    data = {
        'subject_id': range(1, n_subjects + 1),
        'total_sleep_time': np.random.normal(450, 60, n_subjects),  # minutes
        'sleep_efficiency': np.random.normal(0.85, 0.1, n_subjects),
        'sws_duration': np.random.normal(90, 30, n_subjects),  # minutes
        'rem_duration': np.random.normal(100, 25, n_subjects),  # minutes
        'wake_after_sleep_onset': np.random.normal(20, 15, n_subjects),  # minutes
        'sleep_latency': np.random.normal(15, 10, n_subjects)  # minutes
    }
    
    # Ensure non-negative values
    for key in data:
        if key != 'subject_id':
            data[key] = np.maximum(data[key], 0)
    
    return pd.DataFrame(data)

def generate_synthetic_dataset(n_subjects: int = 100, output_path: str = None, seed: int = 42) -> pd.DataFrame:
    """
    Generate a complete synthetic dataset with metagenomic counts and sleep metrics.
    Note: This is for pipeline validation only.
    """
    set_seeds(seed)
    
    predictors, outcomes = load_required_variables()
    
    # Generate metagenomic counts
    microbiome_df = generate_metagenomic_counts(n_subjects, predictors, seed)
    
    # Generate sleep metrics
    sleep_df = generate_sleep_metrics(n_subjects, seed)
    
    # Merge on subject_id
    df = pd.merge(microbiome_df, sleep_df, on='subject_id')
    
    # Ensure output directory exists
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Synthetic dataset saved to {output_path}")
    
    return df

def generate_synthetic_manifest(output_path: str = None, seed: int = 42):
    """
    Generate a synthetic data manifest log.
    Note: This is NOT a Chain-of-Custody log. It is for Constitution Principle I (Reproducibility) for synthetic data validation only.
    """
    set_seeds(seed)
    
    script_path = Path("code/data_generator.py")
    checksum = calculate_script_checksum(script_path) if script_path.exists() else "unknown"
    
    manifest = {
        "schema_version": "schema_v1_synthetic",
        "generation_timestamp": datetime.now().isoformat(),
        "script_checksum": checksum,
        "random_seed": seed,
        "note": "This is a synthetic dataset for pipeline validation. No biological samples were used.",
        "chain_of_custody_log": None  # Explicitly null for synthetic data
    }
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Synthetic manifest saved to {output_path}")
    
    return manifest

def main():
    """
    Main entry point for generating synthetic data.
    """
    parser = argparse.ArgumentParser(description="Synthetic Data Generator")
    parser.add_argument('--n', type=int, default=100, help='Number of subjects')
    parser.add_argument('--output', type=str, default="data/raw/synthetic_data.csv", help='Output file path')
    parser.add_argument('--manifest', type=str, default="data/metadata/synthetic_data_manifest.json", help='Manifest file path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Generate dataset
    print(f"Generating synthetic dataset with {args.n} subjects...")
    generate_synthetic_dataset(n_subjects=args.n, output_path=args.output, seed=args.seed)
    
    # Generate manifest
    print("Generating synthetic data manifest...")
    generate_synthetic_manifest(output_path=args.manifest, seed=args.seed)
    
    print("Synthetic data generation complete.")

if __name__ == "__main__":
    main()
