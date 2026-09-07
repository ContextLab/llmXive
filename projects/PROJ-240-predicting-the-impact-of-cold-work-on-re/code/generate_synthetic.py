import os
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path

# Constants
RANDOM_SEED = 42
N_SAMPLES = 1000

def generate_compositions(n_samples: int, rng: np.random.Generator) -> pd.DataFrame:
    """Generate alloy composition features (Mn, Mg, Si, Cu in wt%)."""
    # Realistic ranges for 5xxx and 6xxx series aluminum alloys
    Mn_wt = rng.uniform(0.0, 1.5, n_samples)
    Mg_wt = rng.uniform(0.5, 5.0, n_samples)
    Si_wt = rng.uniform(0.2, 1.5, n_samples)
    Cu_wt = rng.uniform(0.0, 0.6, n_samples)
    return pd.DataFrame({
        'Mn_wt': Mn_wt,
        'Mg_wt': Mg_wt,
        'Si_wt': Si_wt,
        'Cu_wt': Cu_wt
    })

def generate_cold_work(n_samples: int, rng: np.random.Generator) -> pd.Series:
    """Generate cold work percentage (0-100%)."""
    return rng.uniform(0.0, 100.0, n_samples)

def generate_temperature(n_samples: int, rng: np.random.Generator) -> pd.Series:
    """Generate annealing temperature in Kelvin (400K - 700K)."""
    return rng.uniform(400.0, 700.0, n_samples)

def calculate_time_to_peak(cold_work: pd.Series, compositions: pd.DataFrame, temperature: pd.Series, rng: np.random.Generator) -> pd.Series:
    """
    Calculate time-to-peak softening using a physical kinetics model.
    Model: t_peak = A * exp(Q/RT) * (1 - cold_work/100)^(-n) * (1 + sum(composition_effects))
    """
    R = 8.314  # J/(mol*K)
    Q = 140000  # Activation energy in J/mol (approx for Al recrystallization)
    A = 0.001  # Pre-exponential factor
    n = 2.5  # Cold work exponent

    # Composition effects (simplified linear model based on literature)
    comp_effect = (
        0.5 * compositions['Mn_wt'] +
        0.8 * compositions['Mg_wt'] +
        0.3 * compositions['Si_wt'] +
        0.2 * compositions['Cu_wt']
    )

    # Base kinetics
    base_time = A * np.exp(Q / (R * temperature))

    # Cold work acceleration (more cold work = faster recrystallization)
    cw_factor = (1 - cold_work / 100.0) ** (-n)

    # Composition retardation (solute drag effect)
    comp_factor = 1.0 + comp_effect

    t_peak = base_time * cw_factor * comp_factor

    # Add small physical noise (5% std dev)
    noise = rng.normal(0, 0.05 * t_peak.mean(), n_samples)
    t_peak = t_peak + noise

    # Ensure positive values
    t_peak = np.maximum(t_peak, 1.0)

    return pd.Series(t_peak, name='time_to_peak_min')

def add_noise(data: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Add realistic measurement noise to the dataset."""
    # Small noise for composition (0.01 wt% std dev)
    for col in ['Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']:
        data[col] += rng.normal(0, 0.01, len(data))
        data[col] = np.maximum(data[col], 0.0)

    # Small noise for cold work (0.5% std dev)
    data['cold_work_pct'] += rng.normal(0, 0.5, len(data))
    data['cold_work_pct'] = np.clip(data['cold_work_pct'], 0.0, 100.0)

    # Small noise for temperature (2K std dev)
    data['annealing_temp_K'] += rng.normal(0, 2.0, len(data))
    data['annealing_temp_K'] = np.clip(data['annealing_temp_K'], 400.0, 700.0)

    return data

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Generate synthetic dataset and save to CSV with SHA-256 checksum."""
    # Initialize random generator with seed
    rng = np.random.default_rng(RANDOM_SEED)

    # Generate data
    compositions = generate_compositions(N_SAMPLES, rng)
    cold_work = generate_cold_work(N_SAMPLES, rng)
    temperature = generate_temperature(N_SAMPLES, rng)
    time_to_peak = calculate_time_to_peak(cold_work, compositions, temperature, rng)

    # Assemble dataset
    df = pd.DataFrame({
        'cold_work_pct': cold_work,
        'Mn_wt': compositions['Mn_wt'],
        'Mg_wt': compositions['Mg_wt'],
        'Si_wt': compositions['Si_wt'],
        'Cu_wt': compositions['Cu_wt'],
        'annealing_temp_K': temperature,
        'time_to_peak_min': time_to_peak
    })

    # Add noise
    df = add_noise(df, rng)

    # Ensure output directory exists
    output_dir = Path('data/raw')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'synthetic_baseline.csv'

    # Save to CSV
    df.to_csv(output_path, index=False)

    # Compute and save SHA-256 checksum
    checksum = compute_sha256(output_path)
    checksum_path = output_dir / 'synthetic_baseline.csv.sha256'
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  synthetic_baseline.csv\n")

    print(f"Generated synthetic dataset with {N_SAMPLES} samples to {output_path}")
    print(f"SHA-256 checksum saved to {checksum_path}: {checksum}")

if __name__ == '__main__':
    main()