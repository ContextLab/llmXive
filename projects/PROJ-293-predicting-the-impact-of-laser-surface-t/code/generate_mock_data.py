import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from seed import set_seed, ensure_seed_set

def generate_mock_lst_data(output_path: str, n_records: int = 150, seed: int = 42):
    """
    Generate a deterministic, schema-compliant mock dataset for LST wear resistance.
    
    Args:
        output_path: Path to save the CSV file
        n_records: Number of records to generate (minimum 150)
        seed: Random seed for reproducibility
    """
    ensure_seed_set(seed)
    
    # Define valid categorical values
    pattern_geometries = ['dot', 'line', 'grid', 'honeycomb', 'dimple']
    geometries = ['cylindrical', 'flat', 'spherical']
    
    # Generate base data with physical ranges
    data = {
        'pulse_duration': np.random.uniform(10, 500, n_records),  # ns
        'power': np.random.uniform(50, 1500, n_records),  # W
        'scanning_speed': np.random.uniform(100, 3000, n_records),  # mm/s
        'pattern_geometry': np.random.choice(pattern_geometries, n_records),
        'hardness': np.random.uniform(200, 1500, n_records),  # HV
        'elastic_modulus': np.random.uniform(100, 400, n_records),  # GPa
        'wear_rate': np.random.uniform(0.001, 0.5, n_records),  # mm^3/Nm
        'contact_load': np.random.uniform(5, 50, n_records),  # N
        'sliding_speed': np.random.uniform(0.1, 2.0, n_records),  # m/s
        'density': np.random.uniform(2.5, 8.0, n_records),  # g/cm^3
        'geometry': np.random.choice(geometries, n_records)
    }
    
    df = pd.DataFrame(data)
    
    # Introduce missing values in contact_load and sliding_speed (~15% each)
    # This is specifically for testing T012 logic
    missing_indices_contact = np.random.choice(n_records, size=int(n_records * 0.15), replace=False)
    missing_indices_sliding = np.random.choice(n_records, size=int(n_records * 0.15), replace=False)
    
    # Ensure some overlap but also distinct missing values
    df.loc[missing_indices_contact, 'contact_load'] = np.nan
    df.loc[missing_indices_sliding, 'sliding_speed'] = np.nan
    
    # Ensure required predictors have NO missing values (as per T012 requirements)
    required_predictors = [
        'pulse_duration', 'power', 'scanning_speed', 'pattern_geometry',
        'hardness', 'elastic_modulus'
    ]
    for col in required_predictors:
        df[col] = df[col].fillna(df[col].median())
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    return df

def main():
    """Main entry point for generating mock data."""
    output_path = "data/raw/mock_lst_data.csv"
    print(f"Generating mock LST data to {output_path}...")
    
    df = generate_mock_lst_data(output_path, n_records=150, seed=42)
    
    print(f"Generated {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    print(f"Missing contact_load: {df['contact_load'].isna().sum()}")
    print(f"Missing sliding_speed: {df['sliding_speed'].isna().sum()}")
    print(f"File saved to: {output_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
