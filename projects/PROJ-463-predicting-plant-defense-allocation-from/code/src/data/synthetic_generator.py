"""
Synthetic Data Generator for Structural Validation.

Generates structurally valid synthetic TPM count matrices and metadata
to validate the pipeline when real data is unavailable.

IMPORTANT: This module generates synthetic data ONLY for structural validation.
The data is NOT real biological measurements.
"""
import os
import sys
import json
import hashlib
import datetime
import logging
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_data_path, set_seed
from src.utils.logger import get_logger
from src.utils.schemas import RNASeqStudy

logger = get_logger(__name__)

# Configuration constants
SEED = 42
NUM_SPECIES = 5
NUM_GENES = 1000
NUM_REPLICATES = 3
LOGNORMAL_S = 1.5
LOGNORMAL_SCALE = 10.0
TISSUE_TYPES = ["leaf", "root", "stem"]
TREATMENT_TYPES = ["herbivore_attack", "control", "wounding"]
SPECIES_NAMES = [
    "Arabidopsis thaliana",
    "Solanum lycopersicum",
    "Zea mays",
    "Oryza sativa",
    "Brassica rapa"
]

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_synthetic_tpm_matrix(
    num_samples: int = NUM_SPECIES,
    num_genes: int = NUM_GENES,
    seed: int = SEED
) -> pd.DataFrame:
    """
    Generate a synthetic TPM count matrix.

    A log-normal distribution is used to mimic real expression data patterns.
    """
    set_seed(seed)
    logger.info(f"Generating synthetic TPM matrix with shape: {num_samples} x {num_genes}")

    # Generate gene IDs
    gene_ids = [f"GENE_{i:05d}" for i in range(num_genes)]

    # Generate sample IDs
    sample_ids = [f"SYNTH_SAMPLE_{i:03d}" for i in range(num_samples)]

    # Generate TPM values using log-normal distribution
    # This mimics the heavy-tailed distribution of real gene expression
    tpm_values = stats.lognorm.rvs(
        s=LOGNORMAL_S,
        scale=LOGNORMAL_SCALE,
        size=(num_samples, num_genes),
        random_state=seed
    )

    # Create DataFrame
    df = pd.DataFrame(
        tpm_values,
        index=sample_ids,
        columns=gene_ids
    )

    # Round to reasonable precision for TPM
    df = df.round(4)

    return df

def generate_synthetic_metadata(
    num_samples: int = NUM_SPECIES,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate synthetic metadata consistent with FR-001 requirements.
    """
    set_seed(seed)
    metadata_list = []

    for i in range(num_samples):
        species_name = SPECIES_NAMES[i % len(SPECIES_NAMES)]
        tissue = TISSUE_TYPES[i % len(TISSUE_TYPES)]
        treatment = TREATMENT_TYPES[i % len(TREATMENT_TYPES)]

        study = {
            "accession_id": f"SYNTH_{i:04d}",
            "species": species_name,
            "tissue": tissue,
            "treatment": treatment,
            "replicates": NUM_REPLICATES,
            "mode": "synthetic",
            "real_data_available": False
        }
        metadata_list.append(study)

    return metadata_list

def save_synthetic_manifest(
    file_path: Path,
    checksum: str,
    accession_id: str,
    organism: str
) -> None:
    """
    Write the synthetic data manifest to disk.
    """
    manifest = {
        "file_name": file_path.name,
        "checksum": checksum,
        "source_type": "synthetic",
        "provenance": {
            "generated_at": datetime.datetime.now().isoformat(),
            "tool_versions": {
                "python": f"{sys.version_info.major}.{sys.version_info.minor}",
                "numpy": np.__version__,
                "scipy": stats.__version__
            },
            "accession_id": accession_id,
            "organism": organism
        }
    }

    manifest_path = get_data_path() / "manifests" / "synthetic_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Saved synthetic manifest to {manifest_path}")

def generate_synthetic_metadata_report(
    metadata_list: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Generate the metadata verification report for synthetic data.
    This satisfies T011a input requirements.
    """
    report = {
        "studies": metadata_list
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved synthetic metadata verification report to {output_path}")

def main():
    """
    Main entry point for synthetic data generation.
    """
    logger.info("Starting synthetic data generation...")

    # Ensure directories exist
    raw_data_path = get_data_path() / "raw"
    raw_data_path.mkdir(parents=True, exist_ok=True)

    # Generate TPM matrix
    tpm_df = generate_synthetic_tpm_matrix(
        num_samples=NUM_SPECIES,
        num_genes=NUM_GENES,
        seed=SEED
    )

    # Save TPM matrix to CSV
    tpm_file_name = "SYNTH_TPM_matrix.csv"
    tpm_file_path = raw_data_path / tpm_file_name
    tpm_df.to_csv(tpm_file_path, index=True)

    logger.info(f"Saved synthetic TPM matrix to {tpm_file_path}")

    # Calculate checksum
    checksum = calculate_sha256(tpm_file_path)
    logger.info(f"Calculated checksum: {checksum}")

    # Generate metadata
    metadata_list = generate_synthetic_metadata(
        num_samples=NUM_SPECIES,
        seed=SEED
    )

    # Save synthetic manifest
    save_synthetic_manifest(
        file_path=tpm_file_path,
        checksum=checksum,
        accession_id="SYNTH_001",
        organism="Arabidopsis thaliana"
    )

    # Generate metadata verification report
    report_path = get_data_path() / "processed" / "metadata_verification_report.json"
    generate_synthetic_metadata_report(metadata_list, report_path)

    logger.info("Synthetic data generation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
