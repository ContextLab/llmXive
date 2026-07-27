import os
import sys
import json
import random
import hashlib
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

def set_seeds(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def load_required_variables(config_path: str = "data/config/required_variables.yaml") -> Dict[str, List[str]]:
    """Load required variables from config."""
    import yaml
    if not os.path.exists(config_path):
        # Fallback for testing
        return {'predictors': [f"taxon_{i}" for i in range(10)], 'outcomes': ["sleep_duration", "efficiency"]}
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return {
        'predictors': config.get('predictors', []),
        'outcomes': config.get('outcomes', [])
    }

def generate_large_proxy(
    n_subjects: int = 999,
    taxa_list: Optional[List[str]] = None,
    outcome_list: Optional[List[str]] = None,
    output_path: str = "data/raw/large_proxy.csv"
) -> Dict[str, Any]:
    """
    Generate a verified large proxy dataset (N=999) using the real data schema.
    Explicitly marked as a 'Large Proxy' for stress testing, distinct from T006.
    
    Args:
        n_subjects: Number of subjects (max 999 per Assumption-001)
        taxa_list: List of taxa names
        outcome_list: List of outcome names
        output_path: Path to write the CSV
        
    Returns:
        Metadata dict
    """
    set_seeds()
    
    if taxa_list is None:
        taxa_list = [f"taxon_{i}" for i in range(10)]
    if outcome_list is None:
        outcome_list = ["sleep_duration", "efficiency"]
        
    data = {'subject_id': range(1, n_subjects + 1)}
    
    # Generate predictors
    for taxon in taxa_list:
        counts = np.random.negative_binomial(n=2, p=0.5, size=n_subjects) * 20
        zero_mask = np.random.random(n_subjects) < 0.35
        counts[zero_mask] = 0
        data[taxon] = counts.astype(int)
        
    # Generate outcomes
    for outcome in outcome_list:
        data[outcome] = np.random.normal(10, 2, n_subjects)
        
    df = pd.DataFrame(data)
    
    # Write to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    return {
        "n_subjects": n_subjects,
        "type": "Large Proxy (Stress Test)",
        "output_path": output_path,
        "note": "Synthetic values, real schema. For stress testing only."
    }

def main():
    """Entry point for generating large proxy."""
    parser = argparse.ArgumentParser(description="Generate large proxy dataset for stress testing.")
    parser.add_argument("--n", type=int, default=999, help="Number of subjects")
    parser.add_argument("--output", type=str, default="data/raw/large_proxy.csv", help="Output path")
    args = parser.parse_args()
    
    required_vars = load_required_variables()
    
    result = generate_large_proxy(
        n_subjects=args.n,
        taxa_list=required_vars['predictors'],
        outcome_list=required_vars['outcomes'],
        output_path=args.output
    )
    
    print(f"Large proxy generated: {args.output}")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
