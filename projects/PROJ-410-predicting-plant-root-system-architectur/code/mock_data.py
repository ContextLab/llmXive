import os
import random
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

def generate_mock_dataset(output_dir: Optional[Path] = None) -> None:
    """
    Generate synthetic genomic and phenotypic data for testing and fallback.
    
    Args:
        output_dir: Directory to save the generated data files. Defaults to 'data/raw'.
    """
    if output_dir is None:
        output_dir = Path("data/raw")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set random seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # Generate mock accessions
    num_accessions = 100
    accession_ids = [f"Col-{i:03d}" for i in range(num_accessions)]
    countries = ["Germany", "Sweden", "Finland", "UK", "France", "Spain", "Italy", "Poland", "Netherlands", "Belgium"]
    
    accessions_data = {
        "accession_id": accession_ids,
        "country": [random.choice(countries) for _ in range(num_accessions)],
        "latitude": np.random.uniform(35, 70, num_accessions),
        "longitude": np.random.uniform(-10, 30, num_accessions),
        "collection_year": np.random.randint(1980, 2020, num_accessions)
    }
    
    accessions_df = pd.DataFrame(accessions_data)
    accessions_df.to_csv(output_dir / "accessions.csv", index=False)
    print(f"Generated mock accessions: {output_dir / 'accessions.csv'}")
    
    # Generate mock phenotypes
    # Simulating root system architecture traits under different nutrient conditions
    num_phenotypes = num_accessions * 3  # 3 nutrient conditions
    nutrient_conditions = ["Low_N", "High_N", "Control"]
    
    phenotypes_data = {
        "accession_id": [],
        "nutrient_condition": [],
        "root_length": [],
        "root_angle": [],
        "lateral_root_count": [],
        "branching_density": []
    }
    
    for i in range(num_accessions):
        acc_id = accession_ids[i]
        for condition in nutrient_conditions:
            phenotypes_data["accession_id"].append(acc_id)
            phenotypes_data["nutrient_condition"].append(condition)
            
            # Simulate trait values with some noise and condition effects
            if condition == "Low_N":
                root_length = np.random.normal(15, 3)
                root_angle = np.random.normal(45, 10)
                lateral_root_count = np.random.normal(20, 5)
                branching_density = np.random.normal(0.8, 0.2)
            elif condition == "High_N":
                root_length = np.random.normal(25, 4)
                root_angle = np.random.normal(30, 8)
                lateral_root_count = np.random.normal(35, 7)
                branching_density = np.random.normal(0.5, 0.15)
            else:  # Control
                root_length = np.random.normal(20, 3.5)
                root_angle = np.random.normal(38, 9)
                lateral_root_count = np.random.normal(28, 6)
                branching_density = np.random.normal(0.65, 0.18)
            
            # Ensure positive values
            phenotypes_data["root_length"].append(max(0, root_length))
            phenotypes_data["root_angle"].append(max(0, min(90, root_angle)))
            phenotypes_data["lateral_root_count"].append(max(0, int(lateral_root_count)))
            phenotypes_data["branching_density"].append(max(0, min(1, branching_density)))
    
    phenotypes_df = pd.DataFrame(phenotypes_data)
    phenotypes_df.to_csv(output_dir / "phenotypes.csv", index=False)
    print(f"Generated mock phenotypes: {output_dir / 'phenotypes.csv'}")
    
    print(f"Mock dataset generation complete. Files saved to {output_dir}")