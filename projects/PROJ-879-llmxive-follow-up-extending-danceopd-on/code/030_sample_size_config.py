"""
T030: Read Sample Size from config and write sample_size_config.json.

Loads N_SAMPLES from code/utils/config.py (default 200).
Does NOT run a pilot.
Writes data/results/sample_size_config.json with keys:
  - n_samples: int
  - status: str (e.g., "configured", "adjusted")
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Ensure we can import from the project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config, get_hyperparameter

def load_n_samples() -> int:
    """
    Load N_SAMPLES from config.
    Default is 200 if not present.
    """
    config = get_config()
    # Try to get from hyperparameters or top-level config
    n_samples = config.get("N_SAMPLES")
    if n_samples is None:
        n_samples = config.get("hyperparameters", {}).get("N_SAMPLES")
    
    if n_samples is None:
        n_samples = 200  # Default as per task spec
    
    return int(n_samples)

def check_test_split_size() -> int:
    """
    Estimate test split size based on existing data.
    Returns the number of rows in test_split.parquet if it exists,
    otherwise returns a large default to indicate no constraint.
    """
    test_split_path = project_root / "data" / "processed" / "test_split.parquet"
    if test_split_path.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(test_split_path)
            return len(df)
        except Exception:
            # If we can't read it, assume no constraint
            return float('inf')
    return float('inf')

def write_sample_size_config(n_samples: int, status: str, output_path: Path) -> None:
    """
    Write the sample size configuration to JSON.
    """
    config_data = {
        "n_samples": n_samples,
        "status": status
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(config_data, f, indent=2)

def main() -> None:
    """
    Main entry point for T030.
    """
    # Load N_SAMPLES from config
    n_samples = load_n_samples()
    
    # Check test split size to ensure we don't exceed available data
    test_split_size = check_test_split_size()
    
    status = "configured"
    
    if test_split_size != float('inf') and n_samples > test_split_size:
        n_samples = test_split_size
        status = "adjusted"
    
    # Write output
    output_path = project_root / "data" / "results" / "sample_size_config.json"
    write_sample_size_config(n_samples, status, output_path)
    
    print(f"Sample size configured: {n_samples} (status: {status})")
    print(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()