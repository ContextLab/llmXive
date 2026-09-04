import os
import numpy as np
import pandas as pd
from pathlib import Path

def generate_compositions(n_samples: int, seed: int) -> pd.DataFrame:
    """Generate random alloy compositions."""
    np.random.seed(seed)
    data = {
        'Mn_content': np.random.uniform(0.0, 1.5, n_samples),
        'Mg_content': np.random.uniform(0.0, 1.2, n_samples),
        'Si_content': np.random.uniform(0.0, 0.8, n_samples),
        'Cu_content': np.random.uniform(0.0, 0.5, n_samples)
    }
    return pd.DataFrame(data)

def generate_cold_work(n_samples: int, seed: int) -> pd.Series:
    """Generate cold work percentages."""
    np.random.seed(seed + 1)
    return pd.Series(np.random.uniform(0, 100, n_samples), name='cold_work')

def generate_temperature(n_samples: int, seed: int) -> pd.Series:
    """Generate annealing temperatures in Celsius."""
    np.random.seed(seed + 2)
    return pd.Series(np.random.uniform(200, 450, n_samples), name='annealing_temp')

def calculate_time_to_peak(df: pd.DataFrame, seed: int) -> pd.Series:
    """
    Calculate time-to-peak softening based on a deterministic physical kinetics model.
    Model: t_peak = A * exp(Q / (R * T)) * (1 + k1 * CW + k2 * (CW^2)) * (1 - k3 * Mn - k4 * Mg)
    where:
      A = pre-exponential factor
      Q = activation energy
      R = gas constant
      T = temperature in Kelvin
      CW = cold work
      k1, k2, k3, k4 = kinetic coefficients
    """
    np.random.seed(seed + 3)
    
    # Constants
    A = 1.0e-6
    Q = 142000  # J/mol
    R = 8.314   # J/(mol*K)
    k1 = 0.02
    k2 = 0.0001
    k3 = 0.1
    k4 = 0.15
    
    T_kelvin = df['annealing_temp'] + 273.15
    cw = df['cold_work']
    
    # Base Arrhenius term
    base_time = A * np.exp(Q / (R * T_kelvin))
    
    # Cold work effect (pinning effect increases time)
    cw_effect = 1 + k1 * cw + k2 * (cw ** 2)
    
    # Composition effect (solute drag reduces time)
    comp_effect = 1 - k3 * df['Mn_content'] - k4 * df['Mg_content']
    comp_effect = np.clip(comp_effect, 0.1, 1.0)  # Ensure positive and reasonable
    
    # Calculate time to peak
    time_to_peak = base_time * cw_effect * comp_effect * 3600  # Convert to seconds
    
    return pd.Series(time_to_peak, name='time_to_peak')

def add_noise(df: pd.DataFrame, noise_factor: float = 0.05, seed: int = 42) -> pd.DataFrame:
    """Add Gaussian noise to the time_to_peak."""
    np.random.seed(seed + 4)
    noise = np.random.normal(0, noise_factor * df['time_to_peak'].mean(), len(df))
    df['time_to_peak'] = df['time_to_peak'] + noise
    df['time_to_peak'] = df['time_to_peak'].clip(lower=0.1)  # Ensure positive
    return df

def main():
    """Generate synthetic dataset and save to CSV."""
    n_samples = 200
    seed = 42
    
    # Generate components
    comp_df = generate_compositions(n_samples, seed)
    cw_series = generate_cold_work(n_samples, seed)
    temp_series = generate_temperature(n_samples, seed)
    
    # Combine into single DataFrame
    df = pd.concat([comp_df, cw_series, temp_series], axis=1)
    
    # Calculate time to peak
    df['time_to_peak'] = calculate_time_to_peak(df, seed)
    
    # Add noise
    df = add_noise(df, seed=seed)
    
    # Ensure output directory exists
    output_path = Path('data/raw/synthetic_baseline.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Generated synthetic dataset with {n_samples} samples.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()