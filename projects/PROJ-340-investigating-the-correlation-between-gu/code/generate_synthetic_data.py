import os
import sys
import json
import random
import hashlib
import argparse
import pandas as pd
import numpy as np

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
        'predictors': config.get('predictors', []),
        'outcomes': config.get('outcomes', [])
    }

def generate_metagenomic_counts(n_samples: int, taxa: List[str]) -> pd.DataFrame:
    """
    Generate synthetic metagenomic count data.
    Values are random integers between 10 and 10000 to simulate read counts.
    """
    data = {}
    for taxon in taxa:
        # Simulate sparse data with some zeros
        values = np.random.randint(10, 10000, n_samples)
        # Introduce ~10% zeros
        zero_indices = np.random.choice(n_samples, size=int(n_samples * 0.1), replace=False)
        values[zero_indices] = 0
        data[taxon] = values
    return pd.DataFrame(data)

def generate_sleep_metrics(n_samples: int, metrics: List[str]) -> pd.DataFrame:
    """
    Generate synthetic sleep architecture metrics.
    Values are based on typical physiological ranges.
    """
    data = {}
    for metric in metrics:
        if 'Duration' in metric or 'Time' in metric:
            # Duration in minutes (0 to 600)
            values = np.random.uniform(0, 600, n_samples)
        elif 'Latency' in metric:
            # Latency in minutes (0 to 120)
            values = np.random.uniform(0, 120, n_samples)
        elif 'Efficiency' in metric:
            # Efficiency percentage (0 to 100)
            values = np.random.uniform(40, 100, n_samples)
        else:
            # Generic positive value
            values = np.random.uniform(0, 100, n_samples)
        data[metric] = values
    return pd.DataFrame(data)

def generate_synthetic_dataset(n_samples: int = 100, seed: int = 42) -> pd.DataFrame:
    """
    Generate a complete synthetic dataset with metagenomic counts and sleep metrics.
    """
    set_seeds(seed)
    config_path = 'data/config/required_variables.yaml'
    required_vars = load_required_variables(config_path)
    
    predictors = required_vars['predictors']
    outcomes = required_vars['outcomes']
    
    micro_data = generate_metagenomic_counts(n_samples, predictors)
    sleep_data = generate_sleep_metrics(n_samples, outcomes)
    
    # Add a subject ID
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_samples)]
    combined_data = pd.DataFrame({'subject_id': subject_ids})
    combined_data = pd.concat([combined_data, micro_data, sleep_data], axis=1)
    
    return combined_data

def generate_synthetic_manifest(output_path: str, script_path: str, seed: int = 42):
    """
    Generate a synthetic data manifest log (NOT a Chain of Custody log).
    """
    import hashlib
    
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
    parser.add_argument('--output', type=str, default='data/raw/synthetic_data.csv', help='Output CSV path.')
    parser.add_argument('--manifest', type=str, default='data/metadata/synthetic_data_manifest.json', help='Manifest output path.')
    parser.add_argument('--seed', type=int, default=42, help='Random seed.')
    
    args = parser.parse_args()
    
    df = generate_synthetic_dataset(args.n_samples, args.seed)
    
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"Synthetic data saved to: {args.output}")
    
    generate_synthetic_manifest(args.manifest, __file__, args.seed)
    print(f"Manifest saved to: {args.manifest}")

if __name__ == "__main__":
    main()
