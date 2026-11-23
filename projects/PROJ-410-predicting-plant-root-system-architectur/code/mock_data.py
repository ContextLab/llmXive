import os
import random
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

def generate_mock_dataset(output_dir: Optional[Path] = None, num_accessions: int = 100, num_snps: int = 1000) -> None:
    """
    Generate synthetic genomic and phenotypic data for testing and fallback.
    
    This function generates:
    1. accessions.csv: Metadata for plant accessions (ID, country, coordinates).
    2. phenotypes.csv: Root system architecture traits under different nutrient conditions.
    3. genotypes.csv: SNP data encoded as 0, 1, 2 (homozygous ref, heterozygous, homozygous alt).
    
    Args:
        output_dir: Directory to save the generated data files. Defaults to 'data/raw'.
        num_accessions: Number of accessions to generate.
        num_snps: Number of SNP markers to generate per accession.
    """
    if output_dir is None:
        output_dir = Path("data/raw")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set random seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # --- 1. Generate Mock Accessions ---
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
    
    # --- 2. Generate Mock Phenotypes ---
    # Simulating root system architecture traits under different nutrient conditions
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
            
            # Ensure positive values and logical bounds
            phenotypes_data["root_length"].append(max(0, root_length))
            phenotypes_data["root_angle"].append(max(0, min(90, root_angle)))
            phenotypes_data["lateral_root_count"].append(max(0, int(lateral_root_count)))
            phenotypes_data["branching_density"].append(max(0, min(1, branching_density)))
    
    phenotypes_df = pd.DataFrame(phenotypes_data)
    phenotypes_df.to_csv(output_dir / "phenotypes.csv", index=False)
    print(f"Generated mock phenotypes: {output_dir / 'phenotypes.csv'}")
    
    # --- 3. Generate Mock Genotypes (SNPs) ---
    # Format: accession_id, SNP_1, SNP_2, ..., SNP_N
    # Values: 0 (homozygous ref), 1 (heterozygous), 2 (homozygous alt)
    # Simulating a typical distribution where 0 is most common, 1 less common, 2 least common
    
    snp_columns = [f"SNP_{i:05d}" for i in range(num_snps)]
    genotype_data = {"accession_id": accession_ids}
    
    # Generate genotype matrix: rows=accessions, cols=SNPs
    # Using a multinomial distribution to simulate allele frequencies
    # Probabilities: P(0)=0.7, P(1)=0.2, P(2)=0.1
    probs = [0.7, 0.2, 0.1]
    
    # Generate all SNPs for all accessions
    # Shape: (num_accessions, num_snps)
    genotype_matrix = np.random.choice([0, 1, 2], size=(num_accessions, num_snps), p=probs)
    
    for i, col in enumerate(snp_columns):
        genotype_data[col] = genotype_matrix[:, i]
    
    genotypes_df = pd.DataFrame(genotype_data)
    genotypes_df.to_csv(output_dir / "genotypes.csv", index=False)
    print(f"Generated mock genotypes: {output_dir / 'genotypes.csv'}")
    
    print(f"Mock dataset generation complete. Files saved to {output_dir}")
