import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from seed import set_seed, ensure_seed_set

def generate_mock_lst_data(n_records=150, seed=42):
    """
    Generate a deterministic, schema-compliant mock dataset for LST wear testing.
    
    Args:
        n_records (int): Number of records to generate (minimum 150).
        seed (int): Random seed for reproducibility.
        
    Returns:
        pd.DataFrame: Mock dataset with required columns and realistic distributions.
    """
    set_seed(seed)
    
    # Define valid categories
    valid_patterns = ['dot', 'line', 'grid', 'honeycomb', 'dimple']
    valid_geometries = ['cylindrical', 'flat', 'spherical']
    
    # Generate base features with realistic physical ranges
    pulse_duration = np.random.uniform(10, 500, n_records)  # ns
    power = np.random.uniform(100, 1500, n_records)  # W
    scanning_speed = np.random.uniform(100, 3000, n_records)  # mm/s
    
    # Categorical features
    pattern_geometry = np.random.choice(valid_patterns, n_records)
    geometry = np.random.choice(valid_geometries, n_records)
    
    # Material properties
    hardness = np.random.uniform(200, 1200, n_records)  # HV
    elastic_modulus = np.random.uniform(50, 250, n_records)  # GPa
    density = np.random.uniform(2.5, 8.5, n_records)  # g/cm^3
    
    # Derived wear rate (physically plausible relationship)
    # Higher power/speed -> lower wear, higher hardness -> lower wear
    base_wear = 1e-4
    wear_rate = base_wear * (1000 / power) * (1000 / scanning_speed) * (1000 / hardness) * np.random.lognormal(0, 0.2, n_records)
    wear_rate = np.clip(wear_rate, 1e-7, 1e-2)  # Ensure positive and reasonable range
    
    # Optional load/speed (some missing for T012 testing)
    missing_mask = np.random.random(n_records) < 0.15  # ~15% missing
    contact_load = np.where(missing_mask, np.nan, np.random.uniform(5, 50, n_records))  # N
    sliding_speed = np.where(missing_mask, np.nan, np.random.uniform(0.1, 2.0, n_records))  # m/s
    
    df = pd.DataFrame({
        'pulse_duration': pulse_duration,
        'power': power,
        'scanning_speed': scanning_speed,
        'pattern_geometry': pattern_geometry,
        'hardness': hardness,
        'elastic_modulus': elastic_modulus,
        'wear_rate': wear_rate,
        'contact_load': contact_load,
        'sliding_speed': sliding_speed,
        'density': density,
        'geometry': geometry
    })
    
    return df

def main():
    """Main entry point for mock data generation."""
    output_path = Path("data/raw/mock_lst_data.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df = generate_mock_lst_data(n_records=150, seed=42)
    df.to_csv(output_path, index=False)
    
    print(f"Generated mock dataset with {len(df)} records at {output_path}")
    print(f"Missing contact_load: {df['contact_load'].isna().sum()}")
    print(f"Missing sliding_speed: {df['sliding_speed'].isna().sum()}")

if __name__ == "__main__":
    main()
