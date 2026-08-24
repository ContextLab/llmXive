"""
Script to generate the configuration file for Non-Inferiority testing.

Extracts NON_INFERIORITY_DELTA and RANDOM_SEED from code/src/config.py
and writes them to data/processed/config.json.

This is a prerequisite for T021b (Non-Inferiority Test vs Static k=2).
"""
import json
import os
import sys
from pathlib import Path

# Add the project root to the path to allow imports from code/src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import load_config

def main():
    """Extract config values and write to data/processed/config.json."""
    # Load configuration
    config = load_config()
    
    # Extract required values
    non_inferiority_delta = config.get("NON_INFERIORITY_DELTA")
    random_seed = config.get("RANDOM_SEED")
    
    if non_inferiority_delta is None:
        raise ValueError("NON_INFERIORITY_DELTA not found in config. Please ensure code/src/config.py defines it.")
    
    if random_seed is None:
        raise ValueError("RANDOM_SEED not found in config. Please ensure code/src/config.py defines it.")
    
    # Prepare output data
    output_data = {
        "NON_INFERIORITY_DELTA": non_inferiority_delta,
        "RANDOM_SEED": random_seed
    }
    
    # Ensure output directory exists
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write to JSON file
    output_path = output_dir / "config.json"
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Successfully wrote non-inferiority config to {output_path}")
    print(f"  NON_INFERIORITY_DELTA: {non_inferiority_delta}")
    print(f"  RANDOM_SEED: {random_seed}")

if __name__ == "__main__":
    main()