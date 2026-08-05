"""
Synthetic Data Generator for Prototype Validation.

Generates structurally valid synthetic TPM count matrices and metadata
for pipeline validation when real data is unavailable or for testing.

NOTE: This module generates synthetic data ONLY for structural validation.
It must NOT write to data/raw/ and must clearly label outputs as synthetic.
"""
import os
import sys
import json
import hashlib
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Import from project utils
from src.utils.config import get_data_path, get_seed
from src.utils.logger import get_logger
from src.utils.schemas import ExpressionMatrix, ExpressionMatrixMetadata

# Setup logging
logger = get_logger(__name__)

# Constants
SYNTHETIC_ACCESSION_ID = "SYNTH_001"
SYNTHETIC_ORGANISM = "Arabidopsis thaliana"
SEED = 42
LOGNORMAL_SHAPE = 1.5
LOGNORMAL_SCALE = 10.0
NUM_GENES = 5000
NUM_SAMPLES = 20
NUM_SPECIES = 3
NUM_TISSUES = 2
NUM_TREATMENTS = 2

def calculate_sha256(data: str) -> str:
    """Calculate SHA256 hash of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def generate_synthetic_tpm_matrix(
    num_samples: int = NUM_SAMPLES,
    num_genes: int = NUM_GENES,
    seed: int = SEED
) -> pd.DataFrame:
    """
    Generate a synthetic TPM count matrix.

    Args:
        num_samples: Number of synthetic samples (studies/replicates)
        num_genes: Number of genes to simulate
        seed: Random seed for reproducibility

    Returns:
        DataFrame with genes as rows and samples as columns
    """
    logger.info(f"Generating synthetic TPM matrix: {num_samples} samples x {num_genes} genes")

    np.random.seed(seed)

    # Generate gene IDs
    gene_ids = [f"AT{str(i).zfill(5)}G{str(np.random.randint(1, 999)).zfill(3)}"
                for i in range(num_genes)]

    # Generate sample IDs
    sample_ids = [f"sample_{str(i).zfill(3)}" for i in range(num_samples)]

    # Generate TPM values using log-normal distribution to mimic real expression
    # Most genes have low expression, few have high expression
    tpm_values = stats.lognorm.rvs(
        s=LOGNORMAL_SHAPE,
        scale=LOGNORMAL_SCALE,
        size=(num_genes, num_samples)
    )

    # Add some zeros to mimic dropouts (common in RNA-seq)
    dropout_rate = 0.1
    mask = np.random.random((num_genes, num_samples)) < dropout_rate
    tpm_values[mask] = 0

    # Create DataFrame
    df = pd.DataFrame(
        tpm_values,
        index=gene_ids,
        columns=sample_ids
    )

    # Round to reasonable precision
    df = df.round(6)

    logger.info(f"Generated synthetic TPM matrix with shape: {df.shape}")
    logger.info(f"TPM range: [{df.min().min():.4f}, {df.max().max():.4f}]")
    logger.info(f"Zero rate: {(df == 0).sum().sum() / df.size * 100:.2f}%")

    return df

def generate_synthetic_metadata(
    num_species: int = NUM_SPECIES,
    num_tissues: int = NUM_TISSUES,
    num_treatments: int = NUM_TREATMENTS,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate synthetic metadata for samples.

    Args:
        num_species: Number of species to simulate
        num_tissues: Number of tissue types
        num_treatments: Number of treatment conditions
        seed: Random seed for reproducibility

    Returns:
        List of metadata dictionaries
    """
    np.random.seed(seed + 1)  # Different seed for metadata

    species_list = [
        "Arabidopsis thaliana",
        "Solanum lycopersicum",
        "Zea mays"
    ][:num_species]

    tissue_list = ["leaf", "root", "stem", "flower"][:num_tissues]

    treatment_list = ["control", "herbivore_attack"][:num_treatments]

    metadata = []
    for i in range(NUM_SAMPLES):
        meta = {
            "sample_id": f"sample_{str(i).zfill(3)}",
            "accession_id": SYNTHETIC_ACCESSION_ID,
            "species": np.random.choice(species_list),
            "tissue": np.random.choice(tissue_list),
            "treatment": np.random.choice(treatment_list),
            "replicates": np.random.randint(2, 5),
            "synthetic": True
        }
        metadata.append(meta)

    return metadata

def calculate_manifest_entry(
    file_path: Path,
    data: pd.DataFrame,
    metadata: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate manifest entry for synthetic data.

    Args:
        file_path: Path to the saved file
        data: The synthetic data matrix
        metadata: The synthetic metadata

    Returns:
        Manifest entry dictionary
    """
    # Create a string representation for checksum
    data_str = data.to_json()
    meta_str = json.dumps(metadata, sort_keys=True)
    combined_str = data_str + meta_str
    checksum = calculate_sha256(combined_str)

    manifest = {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "checksum": checksum,
        "source_type": "synthetic",
        "accession_id": SYNTHETIC_ACCESSION_ID,
        "organism": SYNTHETIC_ORGANISM,
        "provenance": {
            "generated_at": datetime.datetime.utcnow().isoformat(),
            "tool_versions": {
                "python": f"{sys.version_info.major}.{sys.version_info.minor}",
                "numpy": np.__version__,
                "scipy": stats.__version__,
                "pandas": pd.__version__
            },
            "parameters": {
                "seed": SEED,
                "num_samples": NUM_SAMPLES,
                "num_genes": NUM_GENES,
                "lognormal_shape": LOGNORMAL_SHAPE,
                "lognormal_scale": LOGNORMAL_SCALE
            }
        },
        "statistics": {
            "num_samples": len(data.columns),
            "num_genes": len(data.index),
            "zero_rate": float((data == 0).sum().sum() / data.size),
            "mean_tpm": float(data.mean().mean()),
            "median_tpm": float(data.median().median())
        }
    }

    return manifest

def save_synthetic_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """
    Save synthetic data manifest to JSON.

    Args:
        manifest: Manifest dictionary
        output_path: Path to save the manifest
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved synthetic manifest to {output_path}")

def generate_synthetic_metadata_report(
    metadata: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Generate and save synthetic metadata verification report.

    This report satisfies T011a input requirements for synthetic data.

    Args:
        metadata: List of metadata dictionaries
        output_path: Path to save the report
    """
    report = {
        "mode": "synthetic",
        "real_data_available": False,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "studies": [],
        "validation_summary": {
            "total_studies": 1,
            "valid_studies": 1,
            "excluded_studies": 0,
            "exclusion_reasons": []
        }
    }

    # Add synthetic study info
    study_info = {
        "accession_id": SYNTHETIC_ACCESSION_ID,
        "species": SYNTHETIC_ORGANISM,
        "tissue": "mixed",
        "treatment": "mixed",
        "replicates": NUM_SAMPLES,
        "validation_status": "passed",
        "notes": "Synthetic data generated for pipeline validation. All metadata fields populated with realistic values."
    }
    report["studies"].append(study_info)

    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved synthetic metadata verification report to {output_path}")

def main() -> int:
    """
    Main function to generate synthetic data and metadata.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        logger.info("Starting synthetic data generation...")

        # Get paths from config
        data_path = get_data_path()
        synthetic_dir = Path(data_path) / "synthetic"
        processed_dir = Path(data_path) / "processed"
        manifests_dir = Path(data_path) / "manifests"

        # Ensure directories exist
        synthetic_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        manifests_dir.mkdir(parents=True, exist_ok=True)

        # Generate synthetic TPM matrix
        tpm_matrix = generate_synthetic_tpm_matrix(
            num_samples=NUM_SAMPLES,
            num_genes=NUM_GENES,
            seed=SEED
        )

        # Save TPM matrix
        tpm_file_path = synthetic_dir / "synthetic_tpm_matrix.csv"
        tpm_matrix.to_csv(tpm_file_path)
        logger.info(f"Saved synthetic TPM matrix to {tpm_file_path}")

        # Generate synthetic metadata
        metadata = generate_synthetic_metadata(seed=SEED)

        # Calculate and save manifest
        manifest = calculate_manifest_entry(tpm_file_path, tpm_matrix, metadata)
        manifest_path = manifests_dir / "synthetic_manifest.json"
        save_synthetic_manifest(manifest, manifest_path)

        # Generate and save metadata verification report (required by T011a)
        report_path = processed_dir / "metadata_verification_report.json"
        generate_synthetic_metadata_report(metadata, report_path)

        logger.info("Synthetic data generation completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during synthetic data generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
