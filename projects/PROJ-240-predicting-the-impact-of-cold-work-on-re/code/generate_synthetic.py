import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np
import pandas as pd

# Hard-coded seed to satisfy Constitution Principle I
HARD_CODED_SEED = 42
MAX_ROWS = 10000


def generate_compositions(n: int, rng: np.random.Generator) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate alloy composition weights (wt%) for Mn, Mg, Si, Cu.
    Ranges based on typical 5xxx/6xxx/7xxx aluminum alloys.
    """
    # Mn: 0.0 to 1.5 wt%
    Mn = rng.uniform(0.0, 1.5, n)
    # Mg: 0.0 to 5.0 wt%
    Mg = rng.uniform(0.0, 5.0, n)
    # Si: 0.0 to 1.2 wt%
    Si = rng.uniform(0.0, 1.2, n)
    # Cu: 0.0 to 2.5 wt%
    Cu = rng.uniform(0.0, 2.5, n)
    return Mn, Mg, Si, Cu


def generate_cold_work(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate cold work percentage (0-100%)."""
    return rng.uniform(0.0, 100.0, n)


def generate_temperature(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate annealing temperature in Kelvin (300K to 700K)."""
    return rng.uniform(300.0, 700.0, n)


def calculate_time_to_peak(
    cold_work: np.ndarray,
    Mn: np.ndarray,
    Mg: np.ndarray,
    Si: np.ndarray,
    Cu: np.ndarray,
    temp: np.ndarray,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Calculate time to peak softening using a deterministic physical kinetics model + noise.
    Model Logic:
    - Higher cold work -> faster recovery (lower time).
    - Higher temp -> faster kinetics (lower time, Arrhenius-like).
    - Alloying elements (Mn, Mg, Si, Cu) generally pin boundaries -> slower kinetics (higher time).
    
    Formula: t = (Base / (CW^0.5 * exp(-Q/RT))) * (1 + k1*Mn + k2*Mg + k3*Si + k4*Cu) + noise
    Simplified for synthetic generation:
    """
    # Constants
    Base = 1000.0
    Activation_energy_factor = 0.005  # Simplified Q/R
    k_Mn, k_Mg, k_Si, k_Cu = 0.5, 0.3, 0.4, 0.6

    # Avoid division by zero or log(0)
    cw_safe = np.maximum(cold_work, 0.1)
    temp_safe = np.maximum(temp, 300.0)

    # Kinetic term: Cold work accelerates, Temperature accelerates
    # CW term: inverse relationship (more work -> less time)
    cw_term = 1.0 / np.sqrt(cw_safe)
    
    # Temp term: Arrhenius-like (higher temp -> less time)
    temp_term = np.exp(-Activation_energy_factor * (1000.0 / temp_safe))

    # Alloying term: additive effect increasing time
    alloy_term = 1.0 + (k_Mn * Mn) + (k_Mg * Mg) + (k_Si * Si) + (k_Cu * Cu)

    # Base calculation
    time_to_peak = Base * cw_term * temp_term * alloy_term

    # Add deterministic noise based on the provided rng
    # Noise magnitude: 10% of the value
    noise = rng.normal(0, 0.1 * time_to_peak)
    time_to_peak += noise

    # Ensure positive time
    time_to_peak = np.maximum(time_to_peak, 1.0)

    return time_to_peak


def add_noise(values: np.ndarray, rng: np.random.Generator, magnitude: float = 0.05) -> np.ndarray:
    """Add small Gaussian noise to values."""
    noise = rng.normal(0, magnitude * np.std(values), values.shape)
    return values + noise


def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    """
    Generate synthetic dataset and save to CSV.
    - Hard-coded seed=42.
    - Cap at 10,000 rows.
    - Compute SHA-256 checksum and write to .sha256 file.
    - Update state YAML with checksum.
    """
    # Initialize RNG with hard-coded seed
    rng = np.random.default_rng(seed=HARD_CODED_SEED)

    # Determine number of samples (cap at MAX_ROWS)
    # For this task, we generate a substantial dataset but respect the cap
    n_samples = 5000 
    if n_samples > MAX_ROWS:
        n_samples = MAX_ROWS

    print(f"Generating synthetic dataset with {n_samples} samples (seed={HARD_CODED_SEED})...")

    # Generate data
    Mn, Mg, Si, Cu = generate_compositions(n_samples, rng)
    cold_work = generate_cold_work(n_samples, rng)
    temp = generate_temperature(n_samples, rng)
    time_to_peak = calculate_time_to_peak(cold_work, Mn, Mg, Si, Cu, temp, rng)

    # Create DataFrame
    df = pd.DataFrame({
        "cold_work_pct": cold_work,
        "Mn_wt": Mn,
        "Mg_wt": Mg,
        "Si_wt": Si,
        "Cu_wt": Cu,
        "annealing_temp_K": temp,
        "time_to_peak_min": time_to_peak
    })

    # Define paths relative to project root
    # Assuming script runs from project root or code directory
    # We need to resolve the project root dynamically
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_raw_dir = project_root / "data" / "raw"
    data_raw_dir.mkdir(parents=True, exist_ok=True)

    csv_path = data_raw_dir / "synthetic_baseline.csv"
    sha_path = data_raw_dir / "synthetic_baseline.csv.sha256"
    state_file = project_root / "state" / "projects" / "PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml"

    # Save CSV
    try:
        df.to_csv(csv_path, index=False)
        print(f"Saved CSV to {csv_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to save CSV: {e}")

    # Compute and save checksum
    try:
        checksum = compute_sha256(str(csv_path))
        # Format: "hash  filename" (two spaces)
        checksum_content = f"{checksum}  synthetic_baseline.csv\n"
        with open(sha_path, "w") as f:
            f.write(checksum_content)
        print(f"Saved checksum to {sha_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to compute or save checksum: {e}")

    # Update state YAML
    try:
        import yaml
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        if state_file.exists():
            with open(state_file, "r") as f:
                state_data = yaml.safe_load(f) or {}
        else:
            state_data = {}

        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}
        
        state_data["artifact_hashes"]["synthetic_baseline_csv"] = checksum

        with open(state_file, "w") as f:
            yaml.dump(state_data, f, default_flow_style=False)
        print(f"Updated state file at {state_file}")
    except ImportError:
        print("Warning: PyYAML not installed. Skipping state file update.")
    except Exception as e:
        raise RuntimeError(f"Failed to update state file: {e}")

    print("Synthetic baseline generation complete.")


if __name__ == "__main__":
    main()
