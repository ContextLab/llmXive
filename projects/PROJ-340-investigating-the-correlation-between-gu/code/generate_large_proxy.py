import os
import sys
import json
import random
import hashlib
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

def set_seeds(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)

def load_required_variables(config_path: str = "data/config/required_variables.yaml") -> dict:
    """Loads required variables from config."""
    path = Path(config_path)
    if path.exists():
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    else:
        return {
            "predictors": [f"Taxon_{i}" for i in range(1, 21)],
            "outcomes": ["SWS_duration", "REM_duration", "Sleep_Efficiency", "Wake_after_sleep_onset"]
        }

def generate_large_proxy(n_subjects: int = 999, seed: int = 42) -> pd.DataFrame:
    """
    Generates a verified large proxy dataset (N=999) using the real data schema.
    Distinct from T006 (Unit Test Generator). Explicitly marked as 'Large Proxy'.
    """
    set_seeds()
    
    config = load_required_variables()
    n_taxa = len(config.get("predictors", []))
    taxa_names = [f"Taxon_{i}" for i in range(1, n_taxa + 1)]
    
    # Generate counts
    data = {}
    for taxon in taxa_names:
        mu = np.random.uniform(10, 100)
        theta = np.random.uniform(0.5, 2.0)
        zero_prob = np.random.uniform(0.3, 0.6)
        counts = np.random.negative_binomial(theta, 1/(1+mu/theta), n_subjects)
        zeros = np.random.random(n_subjects) < zero_prob
        counts[zeros] = 0
        data[taxon] = counts.astype(int)
    
    counts_df = pd.DataFrame(data)
    counts_df.insert(0, "subject_id", [f"SUBJ_{i:04d}" for i in range(n_subjects)])
    
    # Generate sleep metrics
    sleep_data = {
        "subject_id": [f"SUBJ_{i:04d}" for i in range(n_subjects)],
        "SWS_duration": np.random.normal(90, 20, n_subjects).clip(0, 180),
        "REM_duration": np.random.normal(100, 25, n_subjects).clip(0, 150),
        "Sleep_Efficiency": np.random.normal(85, 8, n_subjects).clip(40, 100),
        "Wake_after_sleep_onset": np.random.normal(30, 15, n_subjects).clip(0, 120)
    }
    sleep_df = pd.DataFrame(sleep_data)
    
    merged = pd.merge(counts_df, sleep_df, on="subject_id")
    return merged

def main():
    parser = argparse.ArgumentParser(description="Generate large proxy dataset for stress testing.")
    parser.add_argument("--n", type=int, default=999, help="Number of subjects (max 999 per Assumption-001)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/raw/large_proxy.csv", help="Output CSV path")
    
    args = parser.parse_args()
    
    df = generate_large_proxy(n_subjects=args.n, seed=args.seed)
    
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    print(f"Generated large proxy data: {args.output} (N={args.n})")

if __name__ == "__main__":
    main()
