import os
import sys
import json
import random
import argparse
import numpy as np
from pathlib import Path

_SEED = 42

def set_seeds(seed=42):
    """Set random seeds for reproducibility."""
    global _SEED
    _SEED = seed
    random.seed(seed)
    np.random.seed(seed)

def load_required_variables(config_path='data/config/required_variables.yaml'):
    """Load required variables from config."""
    if os.path.exists(config_path):
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {'required_predictors': [], 'required_outcomes': []}

def save_required_variables(config, output_path='data/config/required_variables.yaml'):
    """Save required variables to config."""
    import yaml
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(config, f)

def generate_metagenomic_counts(n_samples=100, n_taxa=10, seed=42):
    """Generate synthetic metagenomic count data."""
    set_seeds(seed)
    taxa = [f'taxon_{chr(65+i)}' for i in range(n_taxa)]
    data = {}

    for taxon in taxa:
        # Generate count-like data with zero-inflation
        zeros = np.random.binomial(n_samples, 0.3)
        counts = np.random.negative_binomial(2, 0.5, n_samples - zeros)
        values = np.concatenate([np.zeros(zeros), counts])
        np.random.shuffle(values)
        data[taxon] = values.astype(float)

    return data

def generate_sleep_metrics(n_samples=100, seed=42):
    """Generate synthetic sleep architecture metrics."""
    set_seeds(seed)
    metrics = {
        'REM_duration': np.random.normal(90, 20, n_samples),
        'SWS_duration': np.random.normal(120, 30, n_samples),
        'Wake_after_sleep_onset': np.random.normal(20, 10, n_samples)
    }

    # Ensure non-negative
    for key in metrics:
        metrics[key] = np.maximum(metrics[key], 0)

    return metrics

def generate_synthetic_dataset(n_samples=100, seed=42):
    """Generate complete synthetic dataset."""
    import pandas as pd

    metagenomic = generate_metagenomic_counts(n_samples, seed=seed)
    sleep = generate_sleep_metrics(n_samples, seed=seed)

    df_dict = {}
    df_dict.update(metagenomic)
    df_dict.update(sleep)

    df = pd.DataFrame(df_dict)

    # Define required variables
    required_config = {
        'required_predictors': list(metagenomic.keys()),
        'required_outcomes': list(sleep.keys())
    }

    return df, required_config

def generate_synthetic_manifest(df, output_path='data/metadata/synthetic_metadata.json'):
    """Generate metadata manifest for synthetic data."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    manifest = {
        'source': 'synthetic_generator',
        'seed': _SEED,
        'n_samples': len(df),
        'variables': list(df.columns),
        'predictors': [c for c in df.columns if 'taxon' in c.lower()],
        'outcomes': [c for c in df.columns if 'duration' in c.lower() or 'sleep' in c.lower()]
    }

    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest

def main():
    """Main entry point for synthetic data generation."""
    parser = argparse.ArgumentParser(description='Generate synthetic data')
    parser.add_argument('--output', type=str, default='data/raw/synthetic_data.csv')
    parser.add_argument('--n-samples', type=int, default=100)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    set_seeds(args.seed)

    df, required_config = generate_synthetic_dataset(args.n_samples, seed=args.seed)

    # Save data
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df.to_csv(args.output, index=False)

    # Save required variables config
    config_path = 'data/config/required_variables.yaml'
    save_required_variables(required_config, config_path)

    # Generate manifest
    generate_synthetic_manifest(df)

    print(f"Synthetic data generated: {args.output}")
    print(f"Required variables saved to: {config_path}")

if __name__ == '__main__':
    main()
