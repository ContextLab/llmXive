import os
import sys
import json
import random
import hashlib
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

def set_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def load_required_variables(config_path: str) -> Dict[str, List[str]]:
    """Load required variables from config."""
    import yaml
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return {
        'predictors': config.get('required_predictors', []),
        'outcomes': config.get('required_outcomes', [])
    }

def generate_metagenomic_counts(n_samples: int, taxa: List[str], rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate synthetic metagenomic count data.
    Uses Zero-Inflated Negative Binomial distribution logic.
    """
    data = {}
    for taxon in taxa:
        # Simulate counts using Negative Binomial approximation
        # Mean ~ 1000, dispersion ~ 2.0 (arbitrary for synthetic)
        mean_val = 1000.0
        dispersion = 2.0
        
        # Generate counts
        # Using gamma-Poisson mixture for Negative Binomial
        # Gamma shape = mean^2/var, Gamma scale = var/mean
        # For simplicity, use numpy's negative_binomial directly
        # n (number of failures), p (probability of success)
        # Mean = n(1-p)/p, Var = n(1-p)/p^2
        # Let's set mean=1000, var=3000 (overdispersed)
        # n = mean^2 / (var - mean) = 1000000 / 2000 = 500
        # p = n / (n + mean) = 500 / 1500 = 0.333
        n_param = 500
        p_param = 0.333
        
        values = rng.negative_binomial(n_param, p_param, n_samples)
        
        # Introduce Zero-Inflation (~30% zeros as per typical microbiome data)
        zero_mask = rng.random(n_samples) < 0.30
        values[zero_mask] = 0
        
        data[taxon] = values.astype(int)
    return pd.DataFrame(data)

def generate_sleep_metrics(n_samples: int, metrics: List[str], rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate synthetic sleep architecture metrics.
    Values are based on typical physiological ranges (Normal distribution).
    """
    data = {}
    for metric in metrics:
        if 'Duration' in metric or 'Time' in metric:
            # Duration in minutes (Normal distribution around 300-500 mins)
            mean = 400.0
            std = 60.0
            values = rng.normal(mean, std, n_samples)
            values = np.clip(values, 0, 600) # Physiological bounds
        elif 'Latency' in metric:
            # Latency in minutes (Normal distribution, small mean)
            mean = 15.0
            std = 10.0
            values = rng.normal(mean, std, n_samples)
            values = np.clip(values, 0, 120)
        elif 'Efficiency' in metric:
            # Efficiency percentage (Normal, high mean)
            mean = 85.0
            std = 8.0
            values = rng.normal(mean, std, n_samples)
            values = np.clip(values, 0, 100)
        else:
            # Generic positive value
            mean = 50.0
            std = 15.0
            values = rng.normal(mean, std, n_samples)
            values = np.clip(values, 0, 200)
        data[metric] = values
    return pd.DataFrame(data)

def generate_synthetic_dataset(n_samples: int = 100, seed: int = 42, missing_variable: Optional[str] = None) -> pd.DataFrame:
    """
    Generate a complete synthetic dataset with metagenomic counts and sleep metrics.
    Supports injecting a specific missing variable for testing validation logic.
    """
    set_seeds(seed)
    rng = np.random.default_rng(seed)
    
    config_path = 'data/config/required_variables.yaml'
    required_vars = load_required_variables(config_path)
    
    predictors = required_vars['predictors']
    outcomes = required_vars['outcomes']
    
    # Handle missing variable injection
    if missing_variable:
        if missing_variable in outcomes:
            outcomes = [o for o in outcomes if o != missing_variable]
            # Log warning to stderr so the user knows what happened
            print(f"WARNING: Injected missing variable '{missing_variable}' into synthetic dataset.", file=sys.stderr)
        elif missing_variable in predictors:
            predictors = [p for p in predictors if p != missing_variable]
            print(f"WARNING: Injected missing variable '{missing_variable}' into synthetic dataset.", file=sys.stderr)
        else:
            print(f"WARNING: Requested missing variable '{missing_variable}' not found in config, ignoring.", file=sys.stderr)
    
    micro_data = generate_metagenomic_counts(n_samples, predictors, rng)
    sleep_data = generate_sleep_metrics(n_samples, outcomes, rng)
    
    # Add a subject ID
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_samples)]
    combined_data = pd.DataFrame({'subject_id': subject_ids})
    combined_data = pd.concat([combined_data, micro_data, sleep_data], axis=1)
    
    return combined_data

def generate_synthetic_manifest(output_path: str, script_path: str, seed: int = 42):
    """
    Generate a synthetic data manifest log (NOT a Chain of Custody log).
    """
    script_checksum = "calculated_in_T006d" # Placeholder, actual calc in T006d
    
    manifest = {
        "schema_version": "schema_v1_synthetic",
        "generation_seed": seed,
        "script_path": script_path,
        "script_checksum": script_checksum,
        "chain_of_custody_log": None,
        "note": "This is a synthetic dataset for pipeline validation only. Not a biological sample."
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic data for pipeline validation.")
    parser.add_argument('--n-samples', type=int, default=100, help='Number of samples to generate.')
    parser.add_argument('--output', type=str, default='data/raw/synthetic_test_data.csv', help='Output CSV path.')
    parser.add_argument('--manifest', type=str, default='data/metadata/synthetic_data_manifest.json', help='Manifest output path.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed.')
    parser.add_argument('--missing-var', type=str, default=None, help='Name of a variable to omit (for testing T011).')
    
    args = parser.parse_args()
    
    df = generate_synthetic_dataset(args.n_samples, args.seed, args.missing_var)
    
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Synthetic data saved to: {args.output}")
    
    generate_synthetic_manifest(args.manifest, __file__, args.seed)
    print(f"Manifest saved to: {args.manifest}")

if __name__ == "__main__":
    main()