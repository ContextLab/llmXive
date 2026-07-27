"""
Synthetic Data Generator and Manifest Manager.

Generates deterministic synthetic data for pipeline validation.
Enforces Constitution Principle I (Reproducibility) via checksums and schema validation.
"""
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

# --- Configuration & Seeding ---
def set_seeds(seed: int = 42):
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

# --- Checksum Calculation ---
def calculate_script_checksum(script_path: str) -> str:
    """
    Calculate SHA-256 checksum of the generator script itself.
    This ensures the manifest is tied to the exact code version.
    """
    path = Path(script_path)
    if not path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

# --- Validation Logic ---
def check_real_data_flag_and_fail(mode: str):
    """
    Enforces the 'Fail Loudly' rule for real data requests.
    If mode is 'real' but we are in synthetic generation mode, fail immediately.
    """
    if mode == 'real':
        print("CRITICAL: Real data mode requested, but no verified real source is configured in this generator.", file=sys.stderr)
        print("This generator is for synthetic data only. Use --mode synthetic for validation.", file=sys.stderr)
        sys.exit(1)

# --- Data Generation ---
def load_required_variables():
    """
    Loads the list of required variables from the config.
    Used to ensure synthetic data matches the schema.
    """
    config_path = Path("data/config/required_variables.yaml")
    if not config_path.exists():
        # Fallback to defaults if config is missing (for robustness in testing)
        return {
            "predictors": ["Bacteroides", "Firmicutes", "Actinobacteria", "Proteobacteria", "Fusobacteria"],
            "outcomes": ["Sleep Efficiency", "SWS Duration", "REM Duration", "Wake After Sleep Onset"]
        }
    
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def generate_metagenomic_counts(n_subjects: int, taxa: list, seed: int = 42) -> pd.DataFrame:
    """
    Generate mock metagenomic count data.
    Simulates zero-inflated, sparse count data typical of metagenomics.
    """
    set_seeds(seed)
    data = {}
    for taxon in taxa:
        # Simulate zero-inflation: 30% zeros, then log-normal counts
        zeros = np.random.random(n_subjects) < 0.3
        counts = np.random.lognormal(mean=2, sigma=1, size=n_subjects).astype(int)
        counts[zeros] = 0
        data[taxon] = counts
    
    df = pd.DataFrame(data)
    df['subject_id'] = [f'SUBJ_{i:03d}' for i in range(n_subjects)]
    return df

def generate_sleep_metrics(n_subjects: int, outcomes: list, seed: int = 42) -> pd.DataFrame:
    """
    Generate mock sleep architecture metrics.
    """
    set_seeds(seed)
    data = {}
    for metric in outcomes:
        if 'Duration' in metric or 'Efficiency' in metric:
            # Continuous positive values
            if 'Efficiency' in metric:
                data[metric] = np.random.uniform(0.70, 0.95, n_subjects).round(2)
            else:
                data[metric] = np.random.uniform(30, 120, n_subjects).astype(int) # Minutes
        else:
            # General positive values
            data[metric] = np.random.uniform(10, 60, n_subjects).astype(int)
    
    df = pd.DataFrame(data)
    df['subject_id'] = [f'SUBJ_{i:03d}' for i in range(n_subjects)]
    return df

def generate_synthetic_dataset(n_subjects: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Generates a complete synthetic dataset with metagenomic counts and sleep metrics.
    """
    config = load_required_variables()
    taxa = config['predictors']
    outcomes = config['outcomes']
    
    df_micro = generate_metagenomic_counts(n_subjects, taxa, seed)
    df_sleep = generate_sleep_metrics(n_subjects, outcomes, seed)
    
    # Merge on subject_id
    df = pd.merge(df_micro, df_sleep, on='subject_id')
    return df

# --- Manifest Generation ---
def generate_synthetic_manifest(output_path: str, n_subjects: int, seed: int, mode: str = 'synthetic'):
    """
    Generate a synthetic data manifest log.
    This satisfies Constitution Principle I for synthetic data validation.
    
    Enforces schema rules:
      - schema_v1_synthetic: chain_of_custody_log MUST be null.
      - schema_v2_real: chain_of_custody_log MUST be present (not implemented here as we are synthetic).
    """
    script_path = os.path.abspath(__file__)
    checksum = calculate_script_checksum(script_path)
    
    # Determine schema version based on mode
    if mode == 'synthetic':
        schema_version = 'schema_v1_synthetic'
        coc_log = None
        dataset_type = 'synthetic'
    else:
        # If someone tries to call this for real data, it's a logic error in this generator
        raise ValueError("This generator cannot produce real data manifests.")

    manifest = {
        "schema_version": schema_version,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generator_script_checksum": checksum,
        "dataset_type": dataset_type,
        "chain_of_custody_log": coc_log,
        "parameters_used": {
            "n_subjects": n_subjects,
            "random_seed": seed
        },
        "notes": "This is a synthetic dataset for pipeline validation only. No biological samples were used."
    }
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest written to {output_path}")
    return manifest

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data and manifest for pipeline validation.")
    parser.add_argument('--output', type=str, default='data/raw/synthetic_data.csv', help='Output path for CSV data.')
    parser.add_argument('--manifest', type=str, default='data/metadata/synthetic_data_manifest.json', help='Output path for manifest JSON.')
    parser.add_argument('--n', type=int, default=100, help='Number of synthetic subjects.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed.')
    parser.add_argument('--mode', type=str, default='synthetic', choices=['synthetic', 'real'], help='Data mode.')
    
    args = parser.parse_args()
    
    # Enforce real data constraint
    check_real_data_flag_and_fail(args.mode)
    
    # Generate Data
    print(f"Generating synthetic dataset with {args.n} subjects...")
    df = generate_synthetic_dataset(args.n, args.seed)
    
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Data written to {args.output}")
    
    # Generate Manifest
    print("Generating manifest...")
    generate_synthetic_manifest(args.manifest, args.n, args.seed, args.mode)
    
    print("Done.")

if __name__ == "__main__":
    main()
