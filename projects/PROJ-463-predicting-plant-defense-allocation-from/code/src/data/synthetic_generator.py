"""
Synthetic TPM count matrix generator for prototype validation.

Generates structurally valid synthetic data stored in data/synthetic/
(NOT data/raw/). Produces a manifest with checksums and provenance.
"""
import os
import json
import hashlib
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import from existing project modules
from src.utils.config import get_config, get_housekeeping_genes
from src.utils.logger import get_logger
from src.utils.schemas import ManifestEntry, DataManifest, ProvenanceInfo, compute_sha256

logger = get_logger(__name__)

def generate_synthetic_tpm_matrix(
    n_samples: int = 20,
    n_genes: int = 15000,
    n_studies: int = 3,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate a synthetic TPM count matrix with realistic properties.
    
    Args:
        n_samples: Number of samples to generate
        n_genes: Number of genes to generate
        n_studies: Number of distinct studies (for batch effect simulation)
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with genes as rows, samples as columns, TPM values
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generate gene names
    gene_names = [f"GENE_{i:05d}" for i in range(n_genes)]
    
    # Generate sample names with study assignment
    samples_per_study = n_samples // n_studies
    sample_names = []
    study_labels = []
    for i in range(n_studies):
        for j in range(samples_per_study):
            sample_names.append(f"Study{i}_Sample{j}")
            study_labels.append(i)
    
    # Add remaining samples
    remaining = n_samples - len(sample_names)
    for j in range(remaining):
        sample_names.append(f"Study{n_studies}_Sample{j}")
        study_labels.append(n_studies)
    
    # Generate TPM values with realistic distribution
    # Most genes have low expression, few have high expression
    base_expression = np.random.lognormal(mean=1, sigma=2, size=n_genes)
    
    # Create TPM matrix
    tpm_data = np.zeros((n_genes, len(sample_names)))
    
    for i in range(len(sample_names)):
        study = study_labels[i]
        # Add study-specific batch effect
        batch_factor = 1.0 + 0.1 * np.random.randn()
        
        for g in range(n_genes):
            # Base expression + biological variation + technical noise
            expr = base_expression[g] * (1 + 0.2 * np.random.randn()) * batch_factor
            expr = max(0.01, expr)  # Ensure positive values
            tpm_data[g, i] = expr
    
    # Inject housekeeping genes with stable expression
    housekeeping_genes = get_housekeeping_genes()
    hk_indices = []
    for hk_gene in housekeeping_genes[:min(len(housekeeping_genes), 50)]:
        # Find or create housekeeping gene
        if hk_gene in gene_names:
            idx = gene_names.index(hk_gene)
        else:
            idx = n_genes - 1  # Use last gene if not found
            gene_names[idx] = hk_gene
        hk_indices.append(idx)
    
    # Set stable expression for housekeeping genes
    hk_base_value = 50.0  # Moderate TPM
    for idx in hk_indices:
        tpm_data[idx, :] = hk_base_value * (1 + 0.05 * np.random.randn(len(sample_names)))
        tpm_data[idx, :] = np.maximum(0.1, tpm_data[idx, :])
    
    # Create DataFrame
    df = pd.DataFrame(
        tpm_data,
        index=gene_names,
        columns=sample_names
    )
    
    # Add study metadata as a separate attribute for batch correction
    df.attrs['study_labels'] = study_labels[:len(sample_names)]
    
    return df

def calculate_manifest_entry(
    file_path: Path,
    source_type: str = "synthetic"
) -> Dict:
    """
    Calculate checksum and create manifest entry for a generated file.
    
    Args:
        file_path: Path to the generated file
        source_type: Type of data source (default: "synthetic")
    
    Returns:
        Dictionary with file_name, checksum, source_type, and provenance
    """
    checksum = compute_sha256(file_path)
    
    # Get tool versions
    import numpy as np
    import pandas as pd
    import sys
    
    provenance = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "tool_versions": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "numpy": np.__version__,
            "pandas": pd.__version__
        },
        "config": {
            "seed": get_config().seed if hasattr(get_config(), 'seed') else None
        }
    }
    
    return {
        "file_name": file_path.name,
        "checksum": checksum,
        "source_type": source_type,
        "provenance": provenance
    }

def save_synthetic_manifest(
    entries: List[Dict],
    manifest_path: Path
) -> None:
    """
    Save synthetic data manifest to JSON file.
    
    Args:
        entries: List of manifest entry dictionaries
        manifest_path: Path to save the manifest
    """
    manifest_data = {
        "version": "1.0",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "entries": entries
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Saved synthetic manifest to {manifest_path}")

def generate_synthetic_tpm_study(
    output_dir: Path,
    n_samples: int = 20,
    n_genes: int = 15000,
    n_studies: int = 3,
    seed: Optional[int] = None
) -> Dict:
    """
    Generate a complete synthetic TPM study with manifest.
    
    Args:
        output_dir: Directory to save synthetic data
        n_samples: Number of samples
        n_genes: Number of genes
        n_studies: Number of studies
        seed: Random seed
    
    Returns:
        Dictionary with file paths and manifest info
    """
    config = get_config()
    if seed is None:
        seed = config.seed if hasattr(config, 'seed') else 42
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate TPM matrix
    logger.info(f"Generating synthetic TPM matrix: {n_genes} genes, {n_samples} samples")
    tpm_df = generate_synthetic_tpm_matrix(
        n_samples=n_samples,
        n_genes=n_genes,
        n_studies=n_studies,
        seed=seed
    )
    
    # Save TPM matrix
    tpm_file = output_dir / "synthetic_tpm_matrix.csv"
    tpm_df.to_csv(tpm_file)
    logger.info(f"Saved TPM matrix to {tpm_file}")
    
    # Create manifest entry for TPM file
    tpm_entry = calculate_manifest_entry(tpm_file, source_type="synthetic")
    
    # Save metadata
    metadata = {
        "n_samples": n_samples,
        "n_genes": n_genes,
        "n_studies": n_studies,
        "seed": seed,
        "study_labels": tpm_df.attrs.get('study_labels', [])
    }
    
    metadata_file = output_dir / "synthetic_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    metadata_entry = calculate_manifest_entry(metadata_file, source_type="synthetic")
    
    # Create and save manifest
    manifest_path = output_dir.parent / "manifests" / "synthetic_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    save_synthetic_manifest([tpm_entry, metadata_entry], manifest_path)
    
    return {
        "tpm_file": str(tpm_file),
        "metadata_file": str(metadata_file),
        "manifest_file": str(manifest_path),
        "entries": [tpm_entry, metadata_entry]
    }

def main():
    """Main entry point for synthetic data generation."""
    from src.utils.config import get_data_path
    
    logger.info("Starting synthetic TPM data generation")
    
    # Get output directory from config
    synthetic_dir = get_data_path() / "synthetic"
    synthetic_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic study
    result = generate_synthetic_tpm_study(
        output_dir=synthetic_dir,
        n_samples=20,
        n_genes=15000,
        n_studies=3,
        seed=42
    )
    
    logger.info(f"Synthetic data generation complete:")
    logger.info(f"  TPM file: {result['tpm_file']}")
    logger.info(f"  Metadata: {result['metadata_file']}")
    logger.info(f"  Manifest: {result['manifest_file']}")
    
    # Verify files exist
    for key in ['tpm_file', 'metadata_file', 'manifest_file']:
        if not Path(result[key]).exists():
            raise FileNotFoundError(f"Generated file not found: {result[key]}")
    
    logger.info("All synthetic files verified and ready")

if __name__ == "__main__":
    main()
