"""
Helper script to generate dummy interim data for testing T015 locally.
This simulates the output of T014 (preprocess) so T015 can be run.

Run this only for local testing if T014 hasn't been executed yet.
"""
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add code to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

INTERIM_DIR = project_root / "data" / "interim"
INTERIM_DIR.mkdir(parents=True, exist_ok=True)

def generate_dummy_data(material: str, reduction: int, count: int = 10):
    np.random.seed(42)
    return pd.DataFrame({
        'material': [material] * count,
        'reduction': [reduction] * count,
        'confidence': np.random.uniform(0.5, 1.0, count),
        'euler1': np.random.uniform(0, 90, count),
        'euler2': np.random.uniform(0, 90, count),
        'euler3': np.random.uniform(0, 90, count),
        'qx': np.random.uniform(-1, 1, count),
        'qy': np.random.uniform(-1, 1, count),
        'qz': np.random.uniform(-1, 1, count),
        'qw': np.random.uniform(-1, 1, count)
    })

if __name__ == "__main__":
    print("Generating dummy interim data for T015 testing...")
    
    # Al data
    al_df = generate_dummy_data("Al", 20, 50)
    al_df.to_parquet(INTERIM_DIR / "al_20.parquet")
    
    # Cu data
    cu_df = generate_dummy_data("Cu", 60, 30)
    cu_df.to_parquet(INTERIM_DIR / "cu_60.parquet")
    
    # Ni data
    ni_df = generate_dummy_data("Ni", 80, 40)
    ni_df.to_parquet(INTERIM_DIR / "ni_80.parquet")
    
    print(f"Created {len(list(INTERIM_DIR.glob('*.parquet')))} files in {INTERIM_DIR}")
    print("Now you can run: python code/data/consolidate.py")