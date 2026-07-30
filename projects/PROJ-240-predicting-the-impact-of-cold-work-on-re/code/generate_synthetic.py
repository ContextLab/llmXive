"""
Deterministic synthetic data generator for cold work impact on recrystallization kinetics.

Generates data based on a deterministic physical kinetics model (Johnson-Mehl-Avrami-Kolmogorov)
with controlled Gaussian noise, seeded for reproducibility.

Output: data/raw/synthetic_baseline.csv
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure deterministic behavior
SEED = 42
np.random.seed(SEED)

# Constants based on typical aluminum alloy recrystallization physics
# JMAK parameters and material constants
N_SAMPLES = 200  # Number of samples to generate
MIN_COLD_WORK = 0.0
MAX_COLD_WORK = 100.0
MIN_TEMP = 200.0  # Celsius
MAX_TEMP = 500.0  # Celsius

# Alloy composition ranges (weight percent)
MN_RANGE = (0.0, 1.5)
MG_RANGE = (0.0, 1.2)
SI_RANGE = (0.0, 1.0)
CU_RANGE = (0.0, 5.0)

# Physical model constants (simplified for synthetic generation)
# t_peak ~ exp(-k * CW) * (1 + alpha * T) * (1 + beta * composition_effects)
# Where CW is cold work, T is temperature
K_CW = 0.03  # Cold work acceleration factor
ALPHA_T = 0.015  # Temperature acceleration factor
BETA_MN = 0.2
BETA_MG = 0.15
BETA_SI = 0.1
BETA_CU = 0.25
BASE_TIME = 120.0  # Base time in minutes at 0% CW, 200C, pure Al

def generate_compositions(n_samples):
    """Generate realistic alloy compositions within typical ranges."""
    mn = np.random.uniform(MN_RANGE[0], MN_RANGE[1], n_samples)
    mg = np.random.uniform(MG_RANGE[0], MG_RANGE[1], n_samples)
    si = np.random.uniform(SI_RANGE[0], SI_RANGE[1], n_samples)
    cu = np.random.uniform(CU_RANGE[0], CU_RANGE[1], n_samples)
    return mn, mg, si, cu

def generate_cold_work(n_samples):
    """Generate cold work percentages, biased towards typical industrial ranges."""
    # Use a beta distribution to create more samples in the 20-80% range
    cw = np.random.beta(2, 2, n_samples) * (MAX_COLD_WORK - MIN_COLD_WORK) + MIN_COLD_WORK
    return cw

def generate_temperature(n_samples):
    """Generate annealing temperatures."""
    return np.random.uniform(MIN_TEMP, MAX_TEMP, n_samples)

def calculate_time_to_peak(cold_work, temperature, mn, mg, si, cu):
    """
    Calculate time-to-peak softening using a deterministic physical kinetics model.
    
    Model: t_peak = t_base * exp(-k_cw * CW) * (1 + alpha * (T - T_ref)) 
            * (1 + beta_mn * Mn + beta_mg * Mg + beta_si * Si + beta_cu * Cu)
    
    This reflects that:
    - Higher cold work accelerates recrystallization (lower time)
    - Higher temperature accelerates recrystallization (lower time)
    - Alloying elements generally retard recrystallization (increase time)
    """
    # Normalize cold work to 0-1 for the exponential
    cw_norm = cold_work / 100.0
    
    # Temperature effect (linear approximation around reference 200C)
    t_ref = 200.0
    temp_factor = 1.0 + ALPHA_T * (temperature - t_ref)
    
    # Composition retardation factors
    comp_factor = (1.0 + BETA_MN * mn + BETA_MG * mg + 
                  BETA_SI * si + BETA_CU * cu)
    
    # Cold work acceleration (exponential decay)
    cw_factor = np.exp(-K_CW * cw_norm)
    
    # Calculate base time
    time_to_peak = BASE_TIME * cw_factor * temp_factor * comp_factor
    
    return time_to_peak

def add_noise(time_values, noise_level=0.1):
    """Add Gaussian noise to simulate experimental measurement error."""
    noise = np.random.normal(0, noise_level, size=time_values.shape)
    return time_values * (1.0 + noise)

def main():
    """Generate the synthetic dataset and save to CSV."""
    # Create output directory if it doesn't exist
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "synthetic_baseline.csv"
    
    # Generate data
    mn, mg, si, cu = generate_compositions(N_SAMPLES)
    cold_work = generate_cold_work(N_SAMPLES)
    temperature = generate_temperature(N_SAMPLES)
    
    # Calculate time-to-peak using the physical model
    time_to_peak = calculate_time_to_peak(cold_work, temperature, mn, mg, si, cu)
    
    # Add realistic experimental noise (10% std dev)
    time_to_peak_noisy = add_noise(time_to_peak, noise_level=0.1)
    
    # Ensure no negative values
    time_to_peak_noisy = np.maximum(time_to_peak_noisy, 0.1)
    
    # Create DataFrame
    df = pd.DataFrame({
        'sample_id': range(1, N_SAMPLES + 1),
        'cold_work': cold_work,
        'annealing_temp': temperature,
        'Mn_content': mn,
        'Mg_content': mg,
        'Si_content': si,
        'Cu_content': cu,
        'time_to_peak_softening': time_to_peak_noisy
    })
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Generated {N_SAMPLES} samples to {output_path}")
    print(f"Seed used: {SEED}")
    print(f"Time-to-peak range: {df['time_to_peak_softening'].min():.2f} - {df['time_to_peak_softening'].max():.2f} minutes")

if __name__ == "__main__":
    main()
