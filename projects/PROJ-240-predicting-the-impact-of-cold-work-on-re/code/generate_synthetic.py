"""
Generates deterministic synthetic baseline data for recrystallization kinetics.
Uses a physical kinetics model + noise.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any
import pandas as pd
import numpy as np

# Hard-coded seed for reproducibility (Constitution Principle I)
SEED = 42

def generate_compositions(n_samples: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate alloy composition columns (Mn, Mg, Si, Cu) in weight percent.
    Values are small, positive, and realistic for aluminum alloys.
    """
    data = {
        'Mn_wt': rng.uniform(0.0, 1.5, n_samples),
        'Mg_wt': rng.uniform(0.0, 1.2, n_samples),
        'Si_wt': rng.uniform(0.0, 0.8, n_samples),
        'Cu_wt': rng.uniform(0.0, 0.6, n_samples)
    }
    return pd.DataFrame(data)


def generate_cold_work(n_samples: int, rng: np.random.Generator) -> pd.Series:
    """
    Generate cold work percentage (0-100%).
    """
    return pd.Series(rng.uniform(0.0, 100.0, n_samples), name='cold_work_pct')


def generate_temperature(n_samples: int, rng: np.random.Generator) -> pd.Series:
    """
    Generate annealing temperature in Kelvin (300K - 600K).
    """
    return pd.Series(rng.uniform(300.0, 600.0, n_samples), name='annealing_temp_K')


def calculate_time_to_peak(cold_work: pd.Series, compositions: pd.DataFrame, 
                           temperature: pd.Series, rng: np.random.Generator) -> pd.Series:
    """
    Calculate time to peak softening using a simplified Arrhenius-type kinetics model.
    Time ~ exp(Q/RT) / (ColdWork^2 * CompositionSum)
    """
    Q = 140000  # Activation energy J/mol (approx for Al)
    R = 8.314   # Gas constant
    T = temperature.values
    CW = cold_work.values
    
    # Sum of compositions as a proxy for solute drag
    comp_sum = (compositions['Mn_wt'] + compositions['Mg_wt'] + 
                compositions['Si_wt'] + compositions['Cu_wt']).values
    
    # Avoid division by zero
    comp_sum = np.where(comp_sum == 0, 0.01, comp_sum)
    CW = np.where(CW == 0, 0.01, CW)
    
    # Base time calculation
    # Higher temp -> lower time. Higher CW/Comp -> lower time (faster recrystallization)
    time_val = np.exp(Q / (R * T)) / (CW**2 * comp_sum)
    
    # Normalize to reasonable minutes (e.g., 10 to 1000 mins)
    time_val = time_val / time_val.max() * 1000.0 + 10.0
    
    # Add noise
    noise = rng.normal(0, 5.0, size=len(time_val))
    time_val = time_val + noise
    
    # Ensure positive
    time_val = np.maximum(time_val, 1.0)
    
    return pd.Series(time_val, name='time_to_peak_min')


def add_noise(df: pd.DataFrame, rng: np.random.Generator, noise_level: float = 0.05) -> pd.DataFrame:
    """
    Add Gaussian noise to numeric columns to simulate measurement error.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        noise = rng.normal(0, df[col].std() * noise_level, size=len(df))
        df[col] = df[col] + noise
    return df


def compute_sha256(filepath: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def update_state_yaml(checksum: str, filename: str):
    """
    Updates the project state YAML file to record the artifact checksum.
    """
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = state_dir / "PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml"
    
    # Initialize or load existing state
    import yaml
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}
    
    # Ensure structure exists
    if 'artifact_hashes' not in state:
        state['artifact_hashes'] = {}
    
    # Update checksum
    state['artifact_hashes'][filename] = checksum
    
    # Write back
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    print(f"State updated: {state_file}")


def main():
    """
    Main entry point.
    Generates data, saves to CSV, computes checksum, and writes checksum file.
    """
    # Set seed
    rng = np.random.default_rng(SEED)
    
    # Determine output path relative to project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    output_dir = project_root / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_csv = output_dir / "synthetic_baseline.csv"
    checksum_file = output_dir / "synthetic_baseline.csv.sha256"
    
    # Generate data
    # FR-003 & Constitution Principle VII: Cap well under 10k limit
    n_samples = 500 
    print(f"Generating {n_samples} synthetic samples with seed={SEED}...")
    
    compositions = generate_compositions(n_samples, rng)
    cold_work = generate_cold_work(n_samples, rng)
    temperature = generate_temperature(n_samples, rng)
    time_to_peak = calculate_time_to_peak(cold_work, compositions, temperature, rng)
    
    # Combine
    df = pd.concat([cold_work, compositions, temperature, time_to_peak], axis=1)
    
    # Add noise
    df = add_noise(df, rng, noise_level=0.02)
    
    # Save CSV
    df.to_csv(output_csv, index=False)
    print(f"Generated synthetic dataset with {n_samples} rows at {output_csv}")
    
    # Compute and write checksum using hashlib (Python stdlib)
    # The task requires writing the file in `sha256sum` format, 
    # but we compute it internally to avoid subprocess dependency issues in some envs,
    # then format the output exactly as requested.
    checksum = compute_sha256(output_csv)
    
    # Write checksum file in format: "hash  filename" (two spaces)
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  synthetic_baseline.csv\n")
    print(f"Checksum written to {checksum_file}: {checksum}")
    
    # Update state YAML
    try:
        update_state_yaml(checksum, "synthetic_baseline.csv")
    except Exception as e:
        print(f"Warning: Could not update state YAML: {e}")
        # Do not fail the generation if state update fails, but log it.
        raise RuntimeError(f"Generation completed but state update failed: {e}")


if __name__ == "__main__":
    main()
