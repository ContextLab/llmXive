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

def set_seeds(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def load_required_variables() -> tuple:
    """Load required variables from config."""
    config_path = CONFIG_DIR / "required_variables.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('predictors', []), config.get('outcomes', [])

def generate_large_proxy(n_subjects: int = 999, output_path: str = None, seed: int = 42) -> pd.DataFrame:
    """
    Generate a verified large proxy dataset (N=999) using the real data schema.
    Note: Uses N=999 to comply with Assumption-001.
    This is distinct from T006 (Unit Test Generator) and is explicitly marked as a 'Large Proxy'.
    """
    set_seeds(seed)
    
    predictors, outcomes = load_required_variables()
    
    # Generate metagenomic counts
    data = {}
    for taxon in predictors:
        counts = np.random.negative_binomial(n=5, p=0.3, size=n_subjects)
        zero_indices = np.random.choice(n_subjects, size=int(n_subjects * 0.3), replace=False)
        counts[zero_indices] = 0
        data[taxon] = counts
    
    df = pd.DataFrame(data)
    df['subject_id'] = range(1, n_subjects + 1)
    
    # Generate sleep metrics
    for outcome in outcomes:
        if outcome == 'total_sleep_time':
            df[outcome] = np.random.normal(450, 60, n_subjects)
        elif outcome == 'sleep_efficiency':
            df[outcome] = np.random.normal(0.85, 0.1, n_subjects)
        elif outcome == 'sws_duration':
            df[outcome] = np.random.normal(90, 30, n_subjects)
        elif outcome == 'rem_duration':
            df[outcome] = np.random.normal(100, 25, n_subjects)
        elif outcome == 'wake_after_sleep_onset':
            df[outcome] = np.random.normal(20, 15, n_subjects)
        elif outcome == 'sleep_latency':
            df[outcome] = np.random.normal(15, 10, n_subjects)
        else:
            df[outcome] = np.random.normal(50, 20, n_subjects)
    
    # Ensure non-negative values for sleep metrics
    sleep_cols = [c for c in outcomes if c in df.columns]
    for col in sleep_cols:
        df[col] = np.maximum(df[col], 0)
    
    # Ensure output directory exists
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Large proxy dataset saved to {output_path}")
    
    return df

def main():
    """Main entry point for large proxy generator."""
    parser = argparse.ArgumentParser(description="Large Proxy Data Generator")
    parser.add_argument('--n', type=int, default=999, help='Number of subjects')
    parser.add_argument('--output', type=str, default="data/raw/large_proxy.csv", help='Output file path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    print(f"Generating large proxy dataset with {args.n} subjects...")
    generate_large_proxy(n_subjects=args.n, output_path=args.output, seed=args.seed)
    print("Large proxy generation complete.")

if __name__ == "__main__":
    main()
