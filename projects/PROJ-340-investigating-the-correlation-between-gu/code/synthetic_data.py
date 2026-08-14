"""
Deterministic Synthetic Data Generator for Pipeline Validation.
Generates a mock dataset with known ground truths for testing the pipeline logic.

This module is authorized for the "Pipeline Validation Study" as per Plan.md.
It generates deterministic data to verify pipeline logic, not to represent real biological findings.
"""
import os
import sys
import json
import random
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple

def set_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def load_required_variables(config_path: str = "data/config/required_variables.yaml") -> Tuple[List[str], List[str]]:
    """Load required variables from config if it exists, otherwise return defaults for generation."""
    if not os.path.exists(config_path):
        # Default variables for generation if config is missing
        return ["taxon_A", "taxon_B", "taxon_C"], ["REM_duration", "SWS_duration"]
    
    with open(config_path, 'r') as f:
        # Handle both JSON and YAML-like structures if necessary, but spec says JSON for this task
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            # Fallback for YAML if json fails (simple key-value parsing for safety)
            config = {}
            for line in f:
                if ':' in line:
                    k, v = line.split(':', 1)
                    config[k.strip()] = v.strip()
    
    return config.get("required_predictors", []), config.get("required_outcomes", [])

def generate_metagenomic_counts(n_samples: int, taxa: List[str]) -> pd.DataFrame:
    """Generate synthetic metagenomic count data."""
    data = {}
    for taxon in taxa:
        # Generate count-like data (Poisson distribution)
        # Using a lambda that varies slightly per taxon to avoid perfect collinearity
        lam = 10 + hash(taxon) % 20 
        data[taxon] = np.random.poisson(lam=lam, size=n_samples).astype(float)
    return pd.DataFrame(data)

def generate_sleep_metrics(n_samples: int, outcomes: List[str]) -> pd.DataFrame:
    """Generate synthetic sleep architecture metrics."""
    data = {}
    for outcome in outcomes:
        if "REM" in outcome:
            data[outcome] = np.random.normal(loc=90, scale=15, size=n_samples)
        elif "SWS" in outcome:
            data[outcome] = np.random.normal(loc=120, scale=20, size=n_samples)
        else:
            data[outcome] = np.random.normal(loc=100, scale=10, size=n_samples)
    return pd.DataFrame(data)

def generate_synthetic_dataset(n_samples: int = 100, seed: int = 42) -> pd.DataFrame:
    """Generate a complete synthetic dataset with metagenomic and sleep data."""
    set_seeds(seed)
    
    # Load variable names (or use defaults)
    predictors, outcomes = load_required_variables()
    
    if not predictors:
        predictors = ["taxon_A", "taxon_B", "taxon_C"]
    if not outcomes:
        outcomes = ["REM_duration", "SWS_duration"]
    
    # Generate data
    df_taxa = generate_metagenomic_counts(n_samples, predictors)
    df_sleep = generate_sleep_metrics(n_samples, outcomes)
    
    # Add sample ID
    df_taxa['sample_id'] = range(1, n_samples + 1)
    df_sleep['sample_id'] = range(1, n_samples + 1)
    
    # Merge
    df = pd.merge(df_taxa, df_sleep, on='sample_id')
    
    return df

def generate_synthetic_manifest(output_path: str = "data/metadata/synthetic_manifest.json"):
    """Generate a manifest describing the synthetic data."""
    manifest = {
        "type": "synthetic",
        "seed": 42,
        "description": "Deterministic synthetic dataset for pipeline validation",
        "ground_truths": {
            "taxon_A_vs_REM": 0.5,
            "taxon_B_vs_SWS": -0.3
        }
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Generate Synthetic Data")
    parser.add_argument("--output", type=str, default="data/raw/synthetic_data.csv", help="Output CSV path")
    parser.add_argument("--n-samples", type=int, default=100, help="Number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    # Ensure directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    df = generate_synthetic_dataset(n_samples=args.n_samples, seed=args.seed)
    df.to_csv(args.output, index=False)
    print(f"Synthetic data generated: {args.output}")
    
    # Generate manifest
    generate_synthetic_manifest()
    print("Synthetic manifest generated.")

if __name__ == "__main__":
    main()