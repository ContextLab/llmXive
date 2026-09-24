"""
T011: Generate deterministic synthetic baseline data.
Generates data with seed=42, enforces row cap, and saves CSV + SHA256.

CRITICAL: This script generates the PRIMARY data source for the project.
It must fail loudly (raise RuntimeError) if generation fails.
"""
import hashlib
import os
import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any
import pandas as pd
import numpy as np
import yaml

from config import get_project_root, get_max_rows, get_random_seed

def generate_compositions(n_samples: int, seed: int) -> pd.DataFrame:
    """Generate random alloy compositions (Mn, Mg, Si, Cu)."""
    np.random.seed(seed)
    # Typical ranges for 5xxx/6xxx series
    Mn = np.random.uniform(0.0, 1.5, n_samples)
    Mg = np.random.uniform(0.0, 1.2, n_samples)
    Si = np.random.uniform(0.0, 1.2, n_samples)
    Cu = np.random.uniform(0.0, 0.5, n_samples)
    
    return pd.DataFrame({
        'Mn_wt': Mn,
        'Mg_wt': Mg,
        'Si_wt': Si,
        'Cu_wt': Cu
    })

def generate_cold_work(n_samples: int, seed: int) -> pd.Series:
    """Generate random cold work percentages (0-100)."""
    np.random.seed(seed + 1)
    return pd.Series(np.random.uniform(0.0, 100.0, n_samples), name='cold_work_pct')

def generate_temperature(n_samples: int, seed: int) -> pd.Series:
    """Generate random annealing temperatures in Kelvin."""
    np.random.seed(seed + 2)
    # Typical range 300K to 600K
    return pd.Series(np.random.uniform(300.0, 600.0, n_samples), name='annealing_temp_K')

def calculate_time_to_peak(df: pd.DataFrame, seed: int) -> pd.Series:
    """
    Calculate a deterministic 'time to peak' based on features + noise.
    This simulates the physical relationship: higher cold work -> faster kinetics (lower time),
    higher temp -> faster kinetics.
    """
    np.random.seed(seed + 3)
    
    # Base time
    time_peak = 1000.0
    
    # Cold work effect: more work -> less time (inverse relationship)
    time_peak -= df['cold_work_pct'] * 5.0
    
    # Temperature effect: higher temp -> less time
    time_peak -= (df['annealing_temp_K'] - 300) * 2.0
    
    # Alloy effect: Mn slows it down slightly
    time_peak += df['Mn_wt'] * 50.0
    
    # Add noise
    noise = np.random.normal(0, 50, len(df))
    time_peak = time_peak + noise
    
    # Ensure positive
    time_peak = np.maximum(time_peak, 1.0)
    
    return pd.Series(time_peak, name='time_to_peak_min')

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_yaml(checksum: str, file_path: Path):
    """Update the state YAML file with the artifact checksum."""
    project_root = get_project_root()
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = state_dir / "PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml"
    
    # Load existing state or create new
    if state_file.exists():
        with open(state_file, 'r') as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state = {}
    else:
        state = {
            "project_id": "PROJ-240-predicting-the-impact-of-cold-work-on-re",
            "artifact_hashes": {}
        }
    
    # Update checksum
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    state["artifact_hashes"]["synthetic_baseline.csv"] = checksum
    
    # Write back
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    print(f"Updated state file: {state_file}")

def main():
    """Main entry point for T011."""
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = raw_dir / "synthetic_baseline.csv"
    seed = get_random_seed()
    max_rows = get_max_rows()
    
    print(f"Generating synthetic dataset with seed={seed}, max_rows={max_rows}...")
    
    # Enforce hard cap: T011 requires exactly 10000 rows if config allows.
    # We use min(max_rows, 10000) to respect config but ensure we hit the target if possible.
    n_samples = min(max_rows, 10000)
    
    try:
        # Generate data
        compositions = generate_compositions(n_samples, seed)
        cold_work = generate_cold_work(n_samples, seed)
        temperature = generate_temperature(n_samples, seed)
        
        # Combine for time calculation
        df_features = pd.concat([cold_work, compositions, temperature], axis=1)
        time_peak = calculate_time_to_peak(df_features, seed)
        
        # Final combine
        df = pd.concat([cold_work, compositions, temperature, time_peak], axis=1)
        
        # Save
        df.to_csv(output_path, index=False)
        print(f"Generated synthetic dataset with {len(df)} rows at {output_path}")
        
        # Verify row count
        if len(df) != 10000:
            raise RuntimeError(f"Expected 10000 rows, got {len(df)}. Generation failed.")
        
        # Compute checksum
        checksum = compute_sha256(output_path)
        checksum_path = output_path.with_suffix('.csv.sha256')
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        print(f"Checksum saved to {checksum_path}")
        
        # Update state
        update_state_yaml(checksum, output_path)
        
    except Exception as e:
        # Fail loudly: do not fallback to mock data
        raise RuntimeError(f"Synthetic data generation failed: {str(e)}") from e

if __name__ == "__main__":
    main()
