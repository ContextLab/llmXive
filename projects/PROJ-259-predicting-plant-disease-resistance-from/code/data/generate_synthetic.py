"""
Synthetic Data Generator for Plant Disease Resistance Pipeline.

Generates ~150 paired samples (SNPs and Metabolites) with:
- Binary phenotype (balanced split)
- Injected signal structure (effect_size=0.1)
- SNP-Metabolite correlation (0.5)
- Normal noise (0, 1)
- Reproducible seed (42)

Output:
- data/processed/synthetic_snps.csv
- data/processed/synthetic_metabolites.csv
- data/processed/synthetic_phenotypes.csv
- data/data_manifest.yaml (updated with synthetic dataset entry)
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any

# Import project utilities and config
from config import get_path
from utils.logging import get_logger, log_pipeline_step
from data.manifest import add_dataset, load_manifest, update_dataset_status

# Set seed for reproducibility
SEED = 42
np.random.seed(SEED)

# Constants
N_SAMPLES = 150
N_SNPS = 1000
N_METABOLITES = 200
EFFECT_SIZE = 0.1
SNP_METABOLITE_CORR = 0.5
NOISE_STD = 1.0

logger = get_logger(__name__)

def generate_phenotypes(n: int) -> np.ndarray:
    """Generate balanced binary phenotype (0: Susceptible, 1: Resistant)."""
    n_resistant = n // 2
    n_susceptible = n - n_resistant
    phenotypes = np.array([1] * n_resistant + [0] * n_susceptible)
    np.random.shuffle(phenotypes)
    logger.info(f"Generated {n} phenotypes: {n_resistant} Resistant, {n_susceptible} Susceptible")
    return phenotypes

def generate_latent_signal(n: int, effect_size: float) -> np.ndarray:
    """Generate a latent signal vector that drives the phenotype correlation."""
    # Latent signal Z ~ N(0, 1)
    # We will correlate SNPs and Metabolites to Z
    return np.random.normal(0, 1, n)

def generate_snps(n_samples: int, n_features: int, latent_signal: np.ndarray, effect_size: float, corr: float) -> np.ndarray:
    """
    Generate SNP matrix.
    - Base noise ~ N(0, 1)
    - Inject latent signal with correlation 'corr' and scaled by 'effect_size'
    """
    noise = np.random.normal(0, NOISE_STD, (n_samples, n_features))
    # Signal component: latent_signal * effect_size * corr
    # To ensure correlation structure, we mix latent signal into noise
    # X = sqrt(corr^2) * latent + sqrt(1-corr^2) * noise
    # But we also apply effect_size scaling for the "signal strength" relative to phenotype
    # Simplified approach per spec: noise + (latent * effect * corr)
    # Spec says: SNP-metabolite correlation=0.5, effect_size=0.1
    # Let's interpret: The feature values are generated such that they correlate with the latent trait.
    
    # Construct features with correlation to latent signal
    # X_ij = rho * L_i + sqrt(1-rho^2) * N_ij
    rho = corr
    signal_component = latent_signal.reshape(-1, 1) * rho * np.sqrt(2) # Scaling to match variance roughly
    noise_component = np.random.normal(0, np.sqrt(1 - rho**2), (n_samples, n_features))
    
    # Apply effect size scaling to the signal part to control detectability
    # The spec says effect_size=0.1. We apply this to the correlation term.
    X = (signal_component * effect_size) + (noise_component * (1 - effect_size))
    
    # Normalize to standard normal-ish distribution if needed, but keeping variance structure
    return X

def generate_metabolites(n_samples: int, n_features: int, latent_signal: np.ndarray, effect_size: float, corr: float) -> np.ndarray:
    """
    Generate Metabolite matrix.
    Similar logic to SNPs to ensure correlation with latent signal and thus with SNPs.
    """
    rho = corr
    signal_component = latent_signal.reshape(-1, 1) * rho * np.sqrt(2)
    noise_component = np.random.normal(0, np.sqrt(1 - rho**2), (n_samples, n_features))
    
    # Apply effect size
    M = (signal_component * effect_size) + (noise_component * (1 - effect_size))
    return M

def save_to_csv(df: pd.DataFrame, path: Path, description: str):
    """Save dataframe to CSV and log."""
    df.to_csv(path, index=False)
    logger.info(f"Saved {description} to {path} (shape: {df.shape})")

def update_manifest(output_dir: Path, n_snps: int, n_metabolites: int):
    """Update data_manifest.yaml with the new synthetic dataset entry."""
    manifest_path = get_path("data/data_manifest.yaml")
    
    # Load existing manifest or create new
    if manifest_path.exists():
        manifest = load_manifest(manifest_path)
    else:
        manifest = {"datasets": []}

    dataset_id = "synthetic_plant_disease_v1"
    
    # Create dataset entry
    dataset_entry = {
        "id": dataset_id,
        "source_type": "SIMULATED",
        "modality": "multi-omics",
        "n_samples": N_SAMPLES,
        "n_snps": n_snps,
        "n_metabolites": n_metabolites,
        "status": "generated",
        "paths": {
            "snps": str(output_dir / "synthetic_snps.csv"),
            "metabolites": str(output_dir / "synthetic_metabolites.csv"),
            "phenotypes": str(output_dir / "synthetic_phenotypes.csv")
        },
        "metadata": {
            "seed": SEED,
            "effect_size": EFFECT_SIZE,
            "correlation": SNP_METABOLITE_CORR,
            "noise_distribution": "normal(0,1)"
        }
    }

    # Check if exists, update if so
    existing = next((d for d in manifest["datasets"] if d["id"] == dataset_id), None)
    if existing:
        existing.update(dataset_entry)
    else:
        manifest["datasets"].append(dataset_entry)

    from data.manifest import save_manifest
    save_manifest(manifest, manifest_path)
    logger.info(f"Updated manifest at {manifest_path} with dataset {dataset_id}")

def main():
    """Main execution entry point."""
    logger.info("Starting synthetic data generation (Task T009)")
    
    # Ensure output directory exists
    output_dir = get_path("data/processed")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 1. Generate Phenotypes
    phenotypes = generate_phenotypes(N_SAMPLES)
    
    # 2. Generate Latent Signal (driving the correlation)
    latent_signal = generate_latent_signal(N_SAMPLES, EFFECT_SIZE)
    
    # 3. Generate SNPs
    snps_matrix = generate_snps(N_SAMPLES, N_SNPS, latent_signal, EFFECT_SIZE, SNP_METABOLITE_CORR)
    snp_ids = [f"SNP_{i:04d}" for i in range(N_SNPS)]
    snp_df = pd.DataFrame(snps_matrix, columns=snp_ids)
    snp_df.insert(0, "sample_id", [f"sample_{i:03d}" for i in range(N_SAMPLES)])
    
    # 4. Generate Metabolites
    metabo_matrix = generate_metabolites(N_SAMPLES, N_METABOLITES, latent_signal, EFFECT_SIZE, SNP_METABOLITE_CORR)
    metabo_ids = [f"MET_{i:03d}" for i in range(N_METABOLITES)]
    metabo_df = pd.DataFrame(metabo_matrix, columns=metabo_ids)
    metabo_df.insert(0, "sample_id", [f"sample_{i:03d}" for i in range(N_SAMPLES)])
    
    # 5. Create Phenotype DataFrame
    phenotype_df = pd.DataFrame({
        "sample_id": [f"sample_{i:03d}" for i in range(N_SAMPLES)],
        "phenotype": phenotypes
    })
    
    # 6. Save outputs
    snps_path = Path(output_dir) / "synthetic_snps.csv"
    metabo_path = Path(output_dir) / "synthetic_metabolites.csv"
    pheno_path = Path(output_dir) / "synthetic_phenotypes.csv"
    
    save_to_csv(snp_df, snps_path, "SNPs")
    save_to_csv(metabo_df, metabo_path, "Metabolites")
    save_to_csv(phenotype_df, pheno_path, "Phenotypes")
    
    # 7. Update Manifest
    update_manifest(output_dir, N_SNPS, N_METABOLITES)
    
    logger.info("Synthetic data generation completed successfully.")

if __name__ == "__main__":
    main()