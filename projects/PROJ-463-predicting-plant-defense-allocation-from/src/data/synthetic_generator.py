"""
Synthetic TPM count matrix generator for prototype validation.

This module generates structurally valid synthetic TPM matrices to be used
for pipeline validation when real data is not available. It strictly adheres
to the requirement that synthetic data is stored in `data/synthetic/` and
never written to `data/raw/`.

Outputs:
    data/synthetic/synthetic_tpm_matrix.csv: The generated TPM matrix.
    data/synthetic/synthetic_metadata.json: Metadata for the synthetic dataset.
    data/manifests/synthetic_manifest.json: Manifest with checksums and provenance.
"""
import os
import json
import hashlib
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import project utilities
from src.utils.config import get_config, get_housekeeping_genes, get_seed
from src.utils.logger import get_logger
from src.utils.schemas import create_manifest_entry, ProvenanceInfo, DataManifest

logger = get_logger(__name__)
CONFIG = get_config()

def generate_synthetic_tpm_matrix(
    n_genes: int = 15000,
    n_samples: int = 50,
    n_housekeeping: int = None,
    seed: int = None
) -> pd.DataFrame:
    """
    Generate a synthetic TPM count matrix.

    The matrix includes:
    - A fixed set of housekeeping genes with low variance (simulating stable expression).
    - Randomly generated genes with varying expression levels and variances.

    Args:
        n_genes: Total number of genes to generate.
        n_samples: Number of samples (columns).
        n_housekeeping: Number of housekeeping genes to include. If None, uses config.
        seed: Random seed for reproducibility.

    Returns:
        pd.DataFrame: DataFrame with genes as rows and samples as columns.
    """
    if seed is None:
        seed = get_seed()
    np.random.seed(seed)

    housekeeping_genes = get_housekeeping_genes()
    if n_housekeeping is None:
        n_housekeeping = len(housekeeping_genes)
    
    # Ensure we don't exceed total genes
    n_housekeeping = min(n_housekeeping, n_genes)
    n_variable = n_genes - n_housekeeping

    logger.info(f"Generating synthetic matrix: {n_genes} genes, {n_samples} samples "
                f"({n_housekeeping} housekeeping, {n_variable} variable).")

    # 1. Generate Housekeeping Genes (Low variance, stable expression)
    # TPM values typically range 0.1 to 100 for housekeeping, with low CV
    hk_tpm = np.random.lognormal(mean=2.0, sigma=0.3, size=(n_housekeeping, n_samples))
    hk_tpm = np.clip(hk_tpm, 0.1, 200)  # Clamp to reasonable TPM range

    # 2. Generate Variable Genes (Higher variance, some zeros)
    # Mix of low, medium, and high expression
    variable_tpm = np.zeros((n_variable, n_samples))
    
    for i in range(n_variable):
        # Randomly assign expression regime
        regime = np.random.choice(['low', 'medium', 'high'], p=[0.6, 0.3, 0.1])
        if regime == 'low':
            base = np.random.lognormal(mean=0.5, sigma=1.0)
            noise = np.random.lognormal(mean=0, sigma=0.8)
        elif regime == 'medium':
            base = np.random.lognormal(mean=2.5, sigma=1.2)
            noise = np.random.lognormal(mean=0, sigma=1.0)
        else:
            base = np.random.lognormal(mean=4.5, sigma=1.5)
            noise = np.random.lognormal(mean=0, sigma=1.2)
        
        # Add some sample-specific variation
        sample_factor = np.random.uniform(0.5, 1.5, size=n_samples)
        gene_expr = base * noise * sample_factor
        
        # Add sparsity (some zeros)
        zero_prob = np.random.uniform(0.1, 0.4)
        mask = np.random.random(n_samples) > zero_prob
        gene_expr[~mask] = 0
        
        variable_tpm[i] = gene_expr

    # Combine
    all_tpm = np.vstack([hk_tpm, variable_tpm])

    # Create gene IDs
    hk_ids = [f"GENE_{g}" for g in housekeeping_genes[:n_housekeeping]]
    var_ids = [f"GENE_V{i}" for i in range(n_variable)]
    gene_ids = hk_ids + var_ids

    # Create sample IDs
    sample_ids = [f"SAMPLE_{i:03d}" for i in range(n_samples)]

    df = pd.DataFrame(all_tpm, index=gene_ids, columns=sample_ids)
    
    # Ensure non-negative
    df = df.abs()
    
    # Round to 3 decimal places for file cleanliness
    df = df.round(3)

    return df

def calculate_manifest_entry(file_path: str) -> Dict[str, Any]:
    """
    Calculate SHA256 checksum and create a manifest entry for a file.

    Args:
        file_path: Path to the file.

    Returns:
        Dict containing file_name, checksum, source_type, and provenance.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Calculate SHA256
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    checksum = sha256_hash.hexdigest()

    # Get tool versions
    import sys
    import numpy as np
    import pandas as pd
    
    provenance = {
        "generated_at": datetime.datetime.now().isoformat(),
        "tool_versions": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "numpy": np.__version__,
            "pandas": pd.__version__
        }
    }

    return {
        "file_name": path.name,
        "checksum": checksum,
        "source_type": "synthetic",
        "provenance": provenance
    }

def save_synthetic_manifest(manifest_entries: List[Dict[str, Any]], output_path: str):
    """
    Save the synthetic manifest to a JSON file.

    Args:
        manifest_entries: List of manifest entry dictionaries.
        output_path: Path to save the manifest JSON.
    """
    manifest_data = {
        "version": "1.0",
        "source_type": "synthetic",
        "entries": manifest_entries
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Saved synthetic manifest to {output_path}")

def generate_synthetic_tpm_study(
    output_dir: str = None,
    n_genes: int = 15000,
    n_samples: int = 50
):
    """
    Generate a full synthetic study including TPM matrix, metadata, and manifest.

    Args:
        output_dir: Base directory for output. Defaults to CONFIG.DATA_SYNTHETIC_PATH.
        n_genes: Number of genes.
        n_samples: Number of samples.
    """
    if output_dir is None:
        output_dir = str(CONFIG.DATA_SYNTHETIC_PATH)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating synthetic TPM study in {output_path}")

    # 1. Generate Matrix
    tpm_df = generate_synthetic_tpm_matrix(n_genes=n_genes, n_samples=n_samples)
    
    matrix_file = output_path / "synthetic_tpm_matrix.csv"
    tpm_df.to_csv(matrix_file)
    logger.info(f"Saved TPM matrix to {matrix_file}")

    # 2. Generate Metadata
    metadata = {
        "dataset_name": "Synthetic_Plant_Defense_Prototype",
        "description": "Structurally valid synthetic TPM matrix for pipeline validation.",
        "n_genes": len(tpm_df),
        "n_samples": len(tpm_df.columns),
        "generated_at": datetime.datetime.now().isoformat(),
        "parameters": {
            "n_genes": n_genes,
            "n_samples": n_samples,
            "seed": get_seed()
        }
    }
    
    metadata_file = output_path / "synthetic_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_file}")

    # 3. Create Manifest
    manifest_entries = []
    
    # Add TPM Matrix entry
    manifest_entries.append(calculate_manifest_entry(str(matrix_file)))
    
    # Add Metadata entry
    manifest_entries.append(calculate_manifest_entry(str(metadata_file)))

    # Save Manifest to data/manifests/
    manifest_dir = Path(CONFIG.DATA_MANIFESTS_PATH)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = manifest_dir / "synthetic_manifest.json"
    
    save_synthetic_manifest(manifest_entries, str(manifest_file))

    return {
        "matrix": str(matrix_file),
        "metadata": str(metadata_file),
        "manifest": str(manifest_file)
    }

def main():
    """
    CLI entry point for generating synthetic data.
    """
    logger.info("Starting synthetic data generation (T015)...")
    
    try:
        results = generate_synthetic_tpm_study()
        logger.info("Synthetic data generation completed successfully.")
        logger.info(f"Matrix: {results['matrix']}")
        logger.info(f"Metadata: {results['metadata']}")
        logger.info(f"Manifest: {results['manifest']}")
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
