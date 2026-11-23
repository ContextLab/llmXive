import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import load_config

def main():
    """
    Extract NON_INFERIORITY_DELTA and RANDOM_SEED from code/src/config.py
    and write them to data/processed/config.json.
    """
    # Load configuration using the existing loader
    config = load_config()
    
    # Extract required values
    non_inferiority_delta = config.get('NON_INFERIORITY_DELTA')
    random_seed = config.get('RANDOM_SEED')
    
    if non_inferiority_delta is None:
        raise ValueError("NON_INFERIORITY_DELTA not found in configuration")
    if random_seed is None:
        raise ValueError("RANDOM_SEED not found in configuration")
    
    # Prepare output data
    output_data = {
        "NON_INFERIORITY_DELTA": non_inferiority_delta,
        "RANDOM_SEED": random_seed
    }
    
    # Ensure output directory exists
    output_path = project_root / "data" / "processed" / "config.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON file
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Configuration written to {output_path}")
    print(f"  NON_INFERIORITY_DELTA: {non_inferiority_delta}")
    print(f"  RANDOM_SEED: {random_seed}")

if __name__ == "__main__":
    main()
