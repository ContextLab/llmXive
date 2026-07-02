"""
Synthetic data generator for plant disease resistance prediction.

Generates ~150 paired samples with injected signal structure:
- Binary phenotype (balanced split)
- Effect size = 0.1
- Noise distribution = normal(0, 1)
- SNP-metabolite correlation = 0.5
- Seed = 42 for reproducibility

Outputs:
- data/raw/synthetic_snps.csv
- data/raw/synthetic_metabolites.csv
- data/raw/synthetic_phenotypes.csv
- data/data_manifest.yaml (updated with synthetic source)
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path

# Import project utilities
from config import get_path, load_config
from data.manifest import ManifestLoader, load_manifest
from utils.logging import setup_logger, log_pipeline_step

# Set random seed for reproducibility
np.random.seed(42)

# Configuration
N_SAMPLES = 150
N_SNPS = 500
N_METABOLITES = 200
EFFECT_SIZE = 0.1
SNP_METABOLITE_CORR = 0.5
NOISE_STD = 1.0

# Derived values
N_POSITIVE = N_SAMPLES // 2
N_NEGATIVE = N_SAMPLES - N_POSITIVE

def generate_synthetic_data():
    """Generate synthetic multi-omics dataset with injected signal."""
    logger = setup_logger(__name__)
    log_pipeline_step(logger, "generate_synthetic", "Starting synthetic data generation")

    # 1. Generate binary phenotype (balanced)
    phenotype = np.array([0] * N_NEGATIVE + [1] * N_POSITIVE)
    np.random.shuffle(phenotype)

    # Create sample IDs
    sample_ids = [f"sample_{i:04d}" for i in range(N_SAMPLES)]

    # 2. Generate SNP data with signal injection
    # Base SNPs: random noise
    snp_data = np.random.normal(0, 1, size=(N_SAMPLES, N_SNPS))

    # Inject signal: select a subset of SNPs to correlate with phenotype
    n_signal_snps = 20
    signal_snp_indices = np.random.choice(N_SNPS, n_signal_snps, replace=False)

    for idx in signal_snp_indices:
        # Add effect size * phenotype as signal
        snp_data[:, idx] += EFFECT_SIZE * phenotype

    # 3. Generate Metabolite data
    # Base metabolites: random noise
    metab_data = np.random.normal(0, 1, size=(N_SAMPLES, N_METABOLITES))

    # Inject signal: select a subset of metabolites to correlate with phenotype
    n_signal_metabs = 15
    signal_metab_indices = np.random.choice(N_METABOLITES, n_signal_metabs, replace=False)

    for idx in signal_metab_indices:
        # Add effect size * phenotype as signal
        metab_data[:, idx] += EFFECT_SIZE * phenotype

    # 4. Enforce SNP-Metabolite correlation
    # Select a subset of SNPs and metabolites to correlate
    n_correlated = 10
    corr_snp_indices = np.random.choice(N_SNPS, n_correlated, replace=False)
    corr_metab_indices = np.random.choice(N_METABOLITES, n_correlated, replace=False)

    # Create correlated pairs
    for i, (snp_idx, metab_idx) in enumerate(zip(corr_snp_indices, corr_metab_indices)):
        # Generate correlated noise
        u = np.random.normal(0, 1, N_SAMPLES)
        v = SNP_METABOLITE_CORR * u + np.sqrt(1 - SNP_METABOLITE_CORR**2) * np.random.normal(0, 1, N_SAMPLES)

        # Update data
        snp_data[:, snp_idx] = v
        metab_data[:, metab_idx] = u + EFFECT_SIZE * phenotype * 0.5  # Add slight signal too

    # 5. Create DataFrames
    snp_df = pd.DataFrame(
        snp_data,
        columns=[f"snp_{i:04d}" for i in range(N_SNPS)]
    )
    snp_df.insert(0, "sample_id", sample_ids)

    metab_df = pd.DataFrame(
        metab_data,
        columns=[f"metab_{i:04d}" for i in range(N_METABOLITES)]
    )
    metab_df.insert(0, "sample_id", sample_ids)

    phenotype_df = pd.DataFrame({
        "sample_id": sample_ids,
        "phenotype": phenotype,
        "disease_resistance": ["resistant" if p == 1 else "susceptible" for p in phenotype]
    })

    # 6. Save outputs
    config = load_config()
    data_path = get_path("data/raw")

    snp_file = data_path / "synthetic_snps.csv"
    metab_file = data_path / "synthetic_metabolites.csv"
    phenotype_file = data_path / "synthetic_phenotypes.csv"

    snp_df.to_csv(snp_file, index=False)
    metab_df.to_csv(metab_file, index=False)
    phenotype_df.to_csv(phenotype_file, index=False)

    logger.info(f"Generated {N_SAMPLES} samples with {N_SNPS} SNPs and {N_METABOLITES} metabolites")
    logger.info(f"Saved to: {snp_file}, {metab_file}, {phenotype_file}")

    # 7. Update manifest
    manifest_path = get_path("data/data_manifest.yaml")
    update_manifest(manifest_path, snp_file, metab_file, phenotype_file)

    log_pipeline_step(logger, "generate_synthetic", "Synthetic data generation completed successfully")

    return {
        "n_samples": N_SAMPLES,
        "n_snps": N_SNPS,
        "n_metabolites": N_METABOLITES,
        "snp_file": str(snp_file),
        "metab_file": str(metab_file),
        "phenotype_file": str(phenotype_file)
    }

def update_manifest(manifest_path: Path, snp_file: Path, metab_file: Path, phenotype_file: Path):
    """Update data_manifest.yaml with synthetic data source."""
    manifest_data = {
        "version": "1.0",
        "source_type": "SIMULATED",
        "description": "Synthetic plant disease resistance dataset with injected signal",
        "parameters": {
            "n_samples": N_SAMPLES,
            "n_snps": N_SNPS,
            "n_metabolites": N_METABOLITES,
            "effect_size": EFFECT_SIZE,
            "noise_std": NOISE_STD,
            "snp_metabolite_correlation": SNP_METABOLITE_CORR,
            "seed": 42
        },
        "files": {
            "snps": str(snp_file),
            "metabolites": str(metab_file),
            "phenotypes": str(phenotype_file)
        }
    }

    with open(manifest_path, 'w') as f:
        import yaml
        yaml.dump(manifest_data, f, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    generate_synthetic_data()
