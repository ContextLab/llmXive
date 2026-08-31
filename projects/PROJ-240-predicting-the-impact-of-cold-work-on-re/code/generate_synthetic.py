import os
import numpy as np
import pandas as pd
from pathlib import Path

def generate_compositions(n_samples: int, seed: int) -> pd.DataFrame:
    """Generate random alloy compositions within physical bounds."""
    rng = np.random.default_rng(seed)
    data = {
        'Mn_content': rng.uniform(0.0, 1.5, n_samples),
        'Mg_content': rng.uniform(0.0, 1.5, n_samples),
        'Si_content': rng.uniform(0.0, 0.8, n_samples),
        'Cu_content': rng.uniform(0.0, 0.6, n_samples),
    }
    return pd.DataFrame(data)

def generate_cold_work(n_samples: int, seed: int) -> pd.Series:
    """Generate cold work percentages (0-100%)."""
    rng = np.random.default_rng(seed + 1)
    return pd.Series(rng.uniform(0.0, 100.0, n_samples), name='cold_work')

def generate_temperature(n_samples: int, seed: int) -> pd.Series:
    """Generate annealing temperatures (200-500 C)."""
    rng = np.random.default_rng(seed + 2)
    return pd.Series(rng.uniform(200.0, 500.0, n_samples), name='annealing_temp')

def calculate_time_to_peak(df: pd.DataFrame) -> pd.Series:
    """
    Calculate time-to-peak softening using a deterministic physical kinetics model.
    Model: t_peak = A * exp(Q/RT) * (1 - CW)^B * (1 + k*Mn + m*Mg + ...)
    """
    # Constants
    R = 8.314  # J/(mol*K)
    A = 1e-5   # Pre-exponential factor
    Q = 140000 # Activation energy J/mol
    B = 1.5    # Cold work exponent
    
    # Interaction coefficients (simplified physical model)
    k_Mn = 0.2
    k_Mg = 0.15
    k_Si = 0.1
    k_Cu = 0.25

    T_kelvin = df['annealing_temp'] + 273.15
    cw_fraction = df['cold_work'] / 100.0

    # Base kinetics
    base_time = A * np.exp(Q / (R * T_kelvin))
    
    # Cold work effect (reduces time)
    cw_effect = (1 - cw_fraction) ** B
    
    # Composition effect (increases time)
    comp_effect = 1 + (k_Mn * df['Mn_content'] + 
                       k_Mg * df['Mg_content'] + 
                       k_Si * df['Si_content'] + 
                       k_Cu * df['Cu_content'])
    
    return base_time * cw_effect * comp_effect

def add_noise(series: pd.Series, noise_level: float = 0.1, seed: int = 42) -> pd.Series:
    """Add Gaussian noise to the target variable."""
    rng = np.random.default_rng(seed + 3)
    noise = rng.normal(0, noise_level * series.mean(), size=series.shape)
    return series + noise

def main():
    """Generate synthetic baseline dataset and save to CSV."""
    n_samples = 2000
    seed = 42
    
    # Generate features
    comp_df = generate_compositions(n_samples, seed)
    cold_work = generate_cold_work(n_samples, seed)
    temperature = generate_temperature(n_samples, seed)
    
    # Combine features
    df = pd.concat([cold_work, temperature, comp_df], axis=1)
    
    # Calculate target with noise
    df['time_to_peak'] = calculate_time_to_peak(df)
    df['time_to_peak'] = add_noise(df['time_to_peak'], seed=seed)
    
    # Ensure output directory exists
    output_path = Path('data/raw/synthetic_baseline.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} samples saved to {output_path}")

if __name__ == "__main__":
    main()
