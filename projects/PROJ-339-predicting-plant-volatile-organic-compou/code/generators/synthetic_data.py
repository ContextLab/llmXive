"""
Synthetic Data Generator for Arabidopsis VOC Prediction Project.

This module generates a canonical synthetic dataset for *Arabidopsis thaliana*
to serve as a placeholder when real data is unavailable or for testing the
pipeline's ingestion logic.

The generated data is checksummed to ensure integrity and reproducibility.
"""

import os
import random
import hashlib
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

# Ensure we can import sibling utilities if needed, though this module is self-contained
# The API surface requires: generate_synthetic_dataset, main

def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _generate_synthetic_row(
    sample_id: str,
    stress_type: str,
    gene_prefix: str,
    num_genes: int
) -> Dict[str, Any]:
    """
    Generate a single synthetic row of data.

    Args:
        sample_id: Unique identifier for the sample.
        stress_type: Type of stress applied (e.g., 'drought', 'heat').
        gene_prefix: Prefix for gene names (e.g., 'AT1G').
        num_genes: Number of gene expression columns to generate.

    Returns:
        Dictionary representing a single row in the CSV.
    """
    # Environmental metadata (realistic ranges)
    temperature = round(random.uniform(20.0, 35.0), 2)
    light_intensity = round(random.uniform(100.0, 1000.0), 2)
    humidity = round(random.uniform(40.0, 90.0), 2)
    co2_concentration = round(random.uniform(350.0, 450.0), 2)

    # Biological replicates identifier (simulating 3 reps per condition)
    replicate_id = random.randint(1, 3)

    # Gene Expression Data (TPM-like values, log-normal distribution)
    gene_data = {}
    for i in range(num_genes):
        gene_name = f"{gene_prefix}{i+1:04d}A"
        # TPM values are often skewed; use log-normal
        tpm = max(0.0, random.lognormvariate(0, 2))
        gene_data[gene_name] = round(tpm, 4)

    # VOC Target Data (ppb)
    # Simulate correlation with stress type for realism
    base_voc = 50.0
    if stress_type == "drought":
        base_voc += random.uniform(20, 100)
    elif stress_type == "heat":
        base_voc += random.uniform(10, 80)
    elif stress_type == "pathogen":
        base_voc += random.uniform(5, 50)
    
    # Add noise
    voc_target = max(0.0, base_voc + random.gauss(0, 10))

    row = {
        "sample_id": sample_id,
        "organism": "Arabidopsis thaliana",
        "stress_type": stress_type,
        "temperature": temperature,
        "light_intensity": light_intensity,
        "humidity": humidity,
        "co2_concentration": co2_concentration,
        "replicate_id": replicate_id,
        "voc_target_ppb": round(voc_target, 4)
    }
    row.update(gene_data)

    return row

def generate_synthetic_dataset(
    output_path: Path,
    num_samples: int = 100,
    num_genes: int = 50,
    seed: int = 42
) -> Dict[str, str]:
    """
    Generate a synthetic dataset for Arabidopsis VOC prediction.

    Args:
        output_path: Path where the CSV file will be saved.
        num_samples: Number of samples to generate.
        num_genes: Number of gene expression columns per sample.
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing the file path and its SHA-256 checksum.
    """
    random.seed(seed)
    os.makedirs(output_path.parent, exist_ok=True)

    stress_types = ["drought", "heat", "pathogen", "control"]
    gene_prefixes = ["AT1G", "AT2G", "AT3G"]
    
    rows = []
    
    for i in range(num_samples):
        stress = random.choice(stress_types)
        prefix = random.choice(gene_prefixes)
        sample_id = f"AT_{stress}_{i:04d}"
        
        row = _generate_synthetic_row(
            sample_id=sample_id,
            stress_type=stress,
            gene_prefix=prefix,
            num_genes=num_genes
        )
        rows.append(row)

    # Determine header
    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = []

    # Write CSV
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Compute checksum
    checksum = _compute_file_hash(output_path)

    # Create manifest
    manifest_path = output_path.with_suffix('.json')
    manifest_data = {
        "file_path": str(output_path),
        "checksum_algorithm": "sha256",
        "checksum": checksum,
        "num_samples": num_samples,
        "num_genes": num_genes,
        "seed": seed,
        "generated_at": str(Path.cwd()) # Simplified timestamp for manifest
    }

    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)

    return {
        "file": str(output_path),
        "checksum": checksum,
        "manifest": str(manifest_path)
    }

def main():
    """Main entry point for synthetic data generation."""
    # Define paths relative to project root
    # Assuming the script is run from the project root or code/generators
    project_root = Path(__file__).resolve().parent.parent.parent
    output_dir = project_root / "data" / "raw"
    output_file = output_dir / "synthetic_arabidopsis_v1.csv"

    print(f"Generating synthetic dataset to: {output_file}")
    
    try:
        result = generate_synthetic_dataset(
            output_path=output_file,
            num_samples=100,
            num_genes=50,
            seed=42
        )
        
        print(f"Successfully generated dataset.")
        print(f"File: {result['file']}")
        print(f"Checksum: {result['checksum']}")
        print(f"Manifest: {result['manifest']}")
        
    except Exception as e:
        print(f"Error generating synthetic dataset: {e}")
        raise

if __name__ == "__main__":
    main()