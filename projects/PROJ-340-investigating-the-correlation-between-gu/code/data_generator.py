"""
Deterministic Synthetic Data Generator for Pipeline Validation.

This module generates synthetic metagenomic count data and sleep architecture metrics
to validate the pipeline logic without requiring real data access.

CRITICAL: This is a VALIDATION TOOL only. In production, this path must be skipped
in favor of real data fetching (T081).
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

# Set seeds for reproducibility
def set_seeds(seed=42):
    random.seed(seed)
    np.random.seed(seed)

def load_required_variables(config_path="data/config/required_variables.yaml"):
    """
    Reads the required variables from the YAML config.
    Returns lists of predictor and outcome names.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Simple YAML parser for the specific structure expected
    predictors = []
    outcomes = []
    current_section = None
    
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('predictors:'):
                current_section = 'predictors'
                continue
            elif line.startswith('outcomes:'):
                current_section = 'outcomes'
                continue
            
            if current_section and line.startswith('- '):
                var_name = line[2:].strip()
                if current_section == 'predictors':
                    predictors.append(var_name)
                elif current_section == 'outcomes':
                    outcomes.append(var_name)
    
    return predictors, outcomes

def generate_metagenomic_counts(predictors, n_samples=1000):
    """
    Generates synthetic metagenomic count data for the specified predictors.
    Values are simulated as positive floats representing relative abundance or counts.
    """
    data = {}
    for var in predictors:
        # Generate data with some zero-inflation (common in microbiome data)
        # 40% chance of zero, otherwise log-normal distribution
        zeros = np.random.random(n_samples) < 0.4
        non_zeros = ~zeros
        values = np.zeros(n_samples)
        values[non_zeros] = np.random.lognormal(mean=1.0, sigma=1.5, size=non_zeros.sum())
        data[var] = values
    return pd.DataFrame(data)

def generate_sleep_metrics(outcomes, n_samples=1000):
    """
    Generates synthetic sleep architecture metrics for the specified outcomes.
    """
    data = {}
    for var in outcomes:
        if 'Duration' in var or 'Time' in var or 'Latency' in var:
            # Time-based metrics: positive floats
            # Ensure no negative values
            values = np.random.exponential(scale=30.0, size=n_samples)
            values = np.maximum(values, 0.1) # Ensure non-zero
        elif '%' in var:
            # Percentage metrics: 0-100
            values = np.random.beta(2, 5, size=n_samples) * 100
        elif 'Number' in var or 'Index' in var or 'Episodes' in var:
            # Count metrics: non-negative integers
            values = np.random.poisson(lam=5, size=n_samples)
        else:
            # Default: positive float
            values = np.random.exponential(scale=10.0, size=n_samples)
        
        data[var] = values
    return pd.DataFrame(data)

def generate_synthetic_dataset(n_samples=1000, seed=42):
    """
    Generates a complete synthetic dataset combining microbiome and sleep data.
    """
    set_seeds(seed)
    
    # Load variable definitions from config
    try:
        predictors, outcomes = load_required_variables()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    if not predictors or not outcomes:
        print("Error: No predictors or outcomes found in config.")
        sys.exit(1)
    
    # Generate data
    df_predictors = generate_metagenomic_counts(predictors, n_samples)
    df_outcomes = generate_sleep_metrics(outcomes, n_samples)
    
    # Combine
    df = pd.concat([df_predictors, df_outcomes], axis=1)
    
    return df, predictors, outcomes

def generate_synthetic_manifest(df, predictors, outcomes, output_path="data/metadata/synthetic_manifest.json"):
    """
    Generates a manifest file describing the synthetic dataset.
    """
    manifest = {
        "type": "synthetic",
        "seed": 42,
        "n_samples": len(df),
        "predictors": predictors,
        "outcomes": outcomes,
        "ground_truths": {
            # Inject a known correlation for validation
            "taxon_A_vs_REM": 0.5 
        },
        "note": "This is a synthetic dataset for pipeline validation only."
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for pipeline validation.")
    parser.add_argument("--output", type=str, default="data/raw/synthetic_data.csv", help="Output CSV path")
    parser.add_argument("--n_samples", type=int, default=1000, help="Number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Generate data
    df, predictors, outcomes = generate_synthetic_dataset(n_samples=args.n_samples, seed=args.seed)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Write CSV
    df.to_csv(args.output, index=False)
    print(f"Generated synthetic data: {args.output} ({len(df)} rows)")
    
    # Write manifest
    manifest_path = "data/metadata/synthetic_manifest.json"
    generate_synthetic_manifest(df, predictors, outcomes, manifest_path)
    print(f"Generated manifest: {manifest_path}")

if __name__ == "__main__":
    main()
