"""
Synthetic Data Generator for Prototype Validation.

Generates structurally valid synthetic TPM count matrices for Arabidopsis thaliana.
Stores output in data/synthetic/ (NOT data/raw/) and produces a manifest
with checksums and provenance information.

This module is for prototype validation only and MUST NOT write to data/raw/.
"""

import os
import json
import hashlib
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Import existing utilities from the project
from src.utils.config import get_data_path
from src.utils.schemas import ManifestEntry, ProvenanceInfo, DataManifest, ExpressionMatrixMetadata
from src.utils.logger import get_logger

logger = get_logger(__name__)

def generate_synthetic_tpm_matrix(
    n_genes: int = 15000,
    n_samples: int = 10,
    accession_id: str = "SYNTH_001",
    organism: str = "Arabidopsis thaliana",
    seed: Optional[int] = 42
) -> pd.DataFrame:
    """
    Generate a synthetic TPM count matrix.

    Args:
        n_genes: Number of genes to simulate.
        n_samples: Number of samples to simulate.
        accession_id: Synthetic accession identifier.
        organism: Organism name.
        seed: Random seed for reproducibility.

    Returns:
        pd.DataFrame: Synthetic TPM matrix with genes as rows and samples as columns.
    """
    if seed is not None:
        np.random.seed(seed)

    logger.info(f"Generating synthetic TPM matrix: {n_genes} genes, {n_samples} samples")

    # Generate gene IDs (simulating Arabidopsis TAIR10 format)
    gene_ids = [f"AT{np.random.randint(1, 6)}G{np.random.randint(10000, 50000)}" for _ in range(n_genes)]

    # Generate sample names
    sample_names = [f"{accession_id}_S{i+1:03d}" for i in range(n_samples)]

    # Generate TPM values
    # Real RNA-seq data is highly skewed; use log-normal distribution
    # Most genes have low expression, few have high expression
    mean_log_tpm = np.random.normal(loc=2.0, scale=1.5, size=n_genes)
    std_log_tpm = np.abs(np.random.normal(loc=0.8, scale=0.2, size=n_genes))

    # Create matrix with biological variation
    tpm_matrix = np.zeros((n_genes, n_samples))
    for i in range(n_samples):
        # Add sample-specific scaling factor
        scale = np.random.normal(loc=1.0, scale=0.1)
        # Generate expression with gene-specific mean and sample-specific noise
        tpm_matrix[:, i] = np.random.lognormal(mean=mean_log_tpm, sigma=std_log_tpm) * scale

    # Ensure non-negative values
    tpm_matrix = np.maximum(tpm_matrix, 0.001)  # Avoid zero TPM

    # Create DataFrame
    df = pd.DataFrame(
        tpm_matrix,
        index=gene_ids,
        columns=sample_names
    )

    logger.info(f"Synthetic TPM matrix generated with shape: {df.shape}")
    return df

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_manifest_entry(
    file_path: Path,
    accession_id: str,
    organism: str,
    n_genes: int,
    n_samples: int
) -> ManifestEntry:
    """
    Create a manifest entry for the generated synthetic data.

    Args:
        file_path: Path to the generated file.
        accession_id: Synthetic accession identifier.
        organism: Organism name.
        n_genes: Number of genes.
        n_samples: Number of samples.

    Returns:
        ManifestEntry: Validated manifest entry.
    """
    checksum = calculate_sha256(file_path)
    current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Get tool versions
    import numpy
    import pandas
    import src

    provenance = ProvenanceInfo(
        generated_at=current_time,
        tool_versions={
            "python": "3.11",
            "numpy": numpy.__version__,
            "pandas": pandas.__version__,
            "src": getattr(src, "__version__", "unknown")
        },
        accession_id=accession_id,
        organism=organism
    )

    metadata = ExpressionMatrixMetadata(
        n_genes=n_genes,
        n_samples=n_samples,
        source_type="synthetic",
        provenance=provenance
    )

    manifest_entry = ManifestEntry(
        file_name=file_path.name,
        checksum=checksum,
        source_type="synthetic",
        metadata=metadata
    )

    return manifest_entry

def save_synthetic_manifest(manifest_entry: ManifestEntry, output_path: Path) -> None:
    """
    Save the manifest entry to a JSON file.

    Args:
        manifest_entry: The manifest entry to save.
        output_path: Path to the output JSON file.
    """
    # Convert to dict for JSON serialization
    manifest_dict = {
        "file_name": manifest_entry.file_name,
        "checksum": manifest_entry.checksum,
        "source_type": manifest_entry.source_type,
        "provenance": {
            "generated_at": manifest_entry.metadata.provenance.generated_at,
            "tool_versions": manifest_entry.metadata.provenance.tool_versions,
            "accession_id": manifest_entry.metadata.provenance.accession_id,
            "organism": manifest_entry.metadata.provenance.organism
        },
        "metadata": {
            "n_genes": manifest_entry.metadata.n_genes,
            "n_samples": manifest_entry.metadata.n_samples,
            "source_type": manifest_entry.metadata.source_type
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest_dict, f, indent=2)

    logger.info(f"Manifest saved to {output_path}")

def generate_synthetic_tpm_study(
    output_dir: Optional[Path] = None,
    n_genes: int = 15000,
    n_samples: int = 10,
    accession_id: str = "SYNTH_001",
    organism: str = "Arabidopsis thaliana",
    seed: Optional[int] = 42
) -> Dict[str, Any]:
    """
    Generate a complete synthetic TPM study with matrix and manifest.

    Args:
        output_dir: Directory to save outputs. Defaults to data/synthetic/.
        n_genes: Number of genes.
        n_samples: Number of samples.
        accession_id: Synthetic accession identifier.
        organism: Organism name.
        seed: Random seed.

    Returns:
        Dict containing paths to generated files.
    """
    if output_dir is None:
        data_path = get_data_path()
        output_dir = data_path / "synthetic"

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating synthetic study in {output_dir}")

    # Generate matrix
    tpm_df = generate_synthetic_tpm_matrix(
        n_genes=n_genes,
        n_samples=n_samples,
        accession_id=accession_id,
        organism=organism,
        seed=seed
    )

    # Save matrix
    matrix_filename = f"{accession_id}_tpm.csv"
    matrix_path = output_dir / matrix_filename
    tpm_df.to_csv(matrix_path)

    logger.info(f"Saved synthetic TPM matrix to {matrix_path}")

    # Generate and save manifest
    manifest_entry = calculate_manifest_entry(
        file_path=matrix_path,
        accession_id=accession_id,
        organism=organism,
        n_genes=n_genes,
        n_samples=n_samples
    )

    manifest_path = output_dir.parent / "manifests" / "synthetic_manifest.json"
    save_synthetic_manifest(manifest_entry, manifest_path)

    return {
        "matrix_path": str(matrix_path),
        "manifest_path": str(manifest_path),
        "accession_id": accession_id,
        "n_genes": n_genes,
        "n_samples": n_samples
    }

def main():
    """Main entry point for the synthetic generator script."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic TPM count matrices")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory (default: data/synthetic/)")
    parser.add_argument("--n-genes", type=int, default=15000, help="Number of genes to generate")
    parser.add_argument("--n-samples", type=int, default=10, help="Number of samples to generate")
    parser.add_argument("--accession-id", type=str, default="SYNTH_001", help="Synthetic accession ID")
    parser.add_argument("--organism", type=str, default="Arabidopsis thaliana", help="Organism name")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None

    try:
        result = generate_synthetic_tpm_study(
            output_dir=output_dir,
            n_genes=args.n_genes,
            n_samples=args.n_samples,
            accession_id=args.accession_id,
            organism=args.organism,
            seed=args.seed
        )

        print(f"Successfully generated synthetic study:")
        print(f"  Matrix: {result['matrix_path']}")
        print(f"  Manifest: {result['manifest_path']}")
        print(f"  Genes: {result['n_genes']}")
        print(f"  Samples: {result['n_samples']}")

    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        raise

if __name__ == "__main__":
    main()
