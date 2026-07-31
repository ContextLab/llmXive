"""
Synthetic Data Generator for Pipeline Validation.

Generates deterministic synthetic metagenomic count data and sleep metrics
that conform to the project's schema. This is used for pipeline validation
when real data is not available or for testing purposes.

CRITICAL: This module is authorized ONLY for pipeline validation studies.
It must NOT be used to fabricate results for scientific claims.
"""
import os
import sys
import json
import random
import hashlib
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

def set_seeds(seed=42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def load_required_variables(config_path):
    """Load required variables from config."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config.get("required_predictors", []), config.get("required_outcomes", [])
    # Fallback defaults for validation
    return ["Bacteroides", "Firmicutes"], ["SWS duration", "REM duration"]

def generate_metagenomic_counts(n_samples, taxa, seed=42):
    """
    Generate synthetic metagenomic count data.
    Counts are generated from a negative binomial distribution to mimic real data.
    """
    set_seeds(seed)
    data = {}
    for taxon in taxa:
        # Simulate count data with some zeros
        mean = np.random.uniform(10, 100)
        dispersion = np.random.uniform(0.1, 1.0)
        counts = np.random.negative_binomial(dispersion, mean / (mean + dispersion), n_samples)
        # Add some zeros to mimic zero-inflation
        zero_indices = np.random.choice(n_samples, size=int(n_samples * 0.2), replace=False)
        counts[zero_indices] = 0
        data[taxon] = counts
    return pd.DataFrame(data)

def generate_sleep_metrics(n_samples, metrics, seed=42):
    """
    Generate synthetic sleep architecture metrics.
    """
    set_seeds(seed + 1)
    data = {}
    for metric in metrics:
        if "duration" in metric.lower():
            # Duration metrics (minutes)
            mean = np.random.uniform(30, 120)
            std = np.random.uniform(10, 30)
            values = np.random.normal(mean, std, n_samples)
            values = np.clip(values, 0, 300) # Positive values only
        else:
            # Percentage or ratio metrics
            values = np.random.uniform(0, 100, n_samples)
        data[metric] = values
    return pd.DataFrame(data)

def generate_synthetic_dataset(n_samples, required_predictors, required_outcomes, seed=42):
    """
    Generate a complete synthetic dataset.
    """
    set_seeds(seed)
    
    # Generate counts
    counts_df = generate_metagenomic_counts(n_samples, required_predictors, seed)
    
    # Generate sleep metrics
    sleep_df = generate_sleep_metrics(n_samples, required_outcomes, seed)
    
    # Add subject IDs
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_samples)]
    counts_df["subject_id"] = subject_ids
    sleep_df["subject_id"] = subject_ids
    
    # Merge
    df = pd.merge(counts_df, sleep_df, on="subject_id")
    
    # Shuffle
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    return df

def generate_synthetic_manifest(output_path, n_samples, predictors, outcomes, seed=42):
    """Generate a manifest file for the synthetic dataset."""
    manifest = {
        "dataset_type": "synthetic",
        "n_samples": n_samples,
        "predictors": predictors,
        "outcomes": outcomes,
        "seed": seed,
        "generated_at": str(pd.Timestamp.now()),
        "purpose": "Pipeline Validation Only"
    }
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for pipeline validation")
    parser.add_argument("--n_samples", type=int, default=100)
    parser.add_argument("--output", type=str, default="data/raw/synthetic_data.csv")
    parser.add_argument("--config", type=str, default="data/config/research_design.yaml")
    args = parser.parse_args()
    
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Load required variables (simplified for this script)
    # In a real scenario, this would parse the YAML config
    predictors = ["Bacteroides", "Firmicutes", "Actinobacteria"]
    outcomes = ["SWS duration", "REM duration", "Sleep efficiency"]
    
    # Generate data
    df = generate_synthetic_dataset(args.n_samples, predictors, outcomes, seed=42)
    
    # Save
    df.to_csv(args.output, index=False)
    print(f"Generated synthetic data at {args.output} with {args.n_samples} samples.")
    
    # Generate manifest
    manifest_path = str(Path(args.output).with_suffix('.manifest.json'))
    generate_synthetic_manifest(manifest_path, args.n_samples, predictors, outcomes, seed=42)
    print(f"Generated manifest at {manifest_path}")

if __name__ == "__main__":
    main()
