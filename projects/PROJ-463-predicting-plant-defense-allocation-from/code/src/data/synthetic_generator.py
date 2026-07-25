"""
Synthetic TPM count matrix generator for prototype validation.

This module generates structurally valid synthetic TPM matrices and their manifests.
It is designed for testing the pipeline's data ingestion and processing logic
without requiring real biological data.

Constraints:
- Must NOT write to data/raw/
- Must write to data/synthetic/
- Must produce a manifest with checksums and provenance
"""
import os
import json
import hashlib
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import project utilities
from src.utils.config import get_config, get_housekeeping_genes
from src.utils.logger import get_logger
from src.utils.schemas import ProvenanceInfo, ManifestEntry, DataManifest, compute_sha256

logger = get_logger(__name__)

def generate_synthetic_tpm_matrix(
    n_genes: int = 20000,
    n_samples: int = 50,
    n_housekeeping: Optional[int] = None,
    seed: Optional[int] = None,
    tissue_types: Optional[List[str]] = None,
    herbivore_types: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Generate a synthetic TPM count matrix with realistic biological properties.
    
    Args:
        n_genes: Total number of genes to simulate
        n_samples: Number of samples to simulate
        n_housekeeping: Number of housekeeping genes (if None, uses config)
        seed: Random seed for reproducibility
        tissue_types: List of tissue types to include in metadata
        herbivore_types: List of herbivore types to include in metadata
        
    Returns:
        pd.DataFrame: Synthetic TPM matrix with genes as rows, samples as columns
    """
    if seed is not None:
        np.random.seed(seed)
        
    config = get_config()
    housekeeping_genes = get_housekeeping_genes()
    
    if n_housekeeping is None:
        n_housekeeping = len(housekeeping_genes)
        
    if tissue_types is None:
        tissue_types = ["leaf", "root", "stem", "flower"]
        
    if herbivore_types is None:
        herbivore_types = ["chewing", "sucking", "none"]
        
    logger.info(f"Generating synthetic TPM matrix: {n_genes} genes, {n_samples} samples")
    logger.info(f"Using {n_housekeeping} housekeeping genes for structure")
    
    # Generate gene names
    # First, use the actual housekeeping gene names from config
    gene_names = list(housekeeping_genes[:n_housekeeping])
    
    # Fill remaining with synthetic gene names
    remaining_genes = n_genes - n_housekeeping
    synthetic_gene_names = [f"Gene_{i:05d}" for i in range(remaining_genes)]
    gene_names.extend(synthetic_gene_names)
    
    # Generate sample names with tissue and herbivore metadata
    sample_names = []
    for i in range(n_samples):
        tissue = tissue_types[i % len(tissue_types)]
        herbivore = herbivore_types[i % len(herbivore_types)]
        sample_name = f"Sample_{i:03d}_{tissue}_{herbivore}"
        sample_names.append(sample_name)
    
    # Generate TPM values with realistic distribution
    # Housekeeping genes should have lower variance
    # Most genes should have low expression, few highly expressed
    
    tpm_matrix = np.zeros((n_genes, n_samples))
    
    # Generate base expression levels (log-normal distribution)
    # Most genes have low expression, few have high
    base_expression = np.random.lognormal(mean=2, sigma=1.5, size=n_genes)
    
    # Housekeeping genes have stable expression (lower variance)
    hk_indices = list(range(n_housekeeping))
    for idx in hk_indices:
        # Housekeeping genes: mean ~50 TPM, low variance
        base_expression[idx] = np.random.lognormal(mean=3.9, sigma=0.3)
    
    # Generate sample-specific factors (batch effects, library size)
    sample_factors = np.random.lognormal(mean=0, sigma=0.5, size=n_samples)
    
    # Add tissue-specific effects
    tissue_effect = {}
    for tissue in tissue_types:
        tissue_effect[tissue] = np.random.lognormal(mean=0, sigma=0.3, size=n_genes)
    
    # Add herbivore-specific effects (differential expression)
    herbivore_effect = {}
    for herbivore in herbivore_types:
        herbivore_effect[herbivore] = np.random.lognormal(mean=0, sigma=0.2, size=n_genes)
    
    # Construct the matrix
    for i in range(n_samples):
        sample_name = sample_names[i]
        # Parse tissue and herbivore from sample name
        parts = sample_name.split("_")
        tissue = parts[2]
        herbivore = parts[3]
        
        # Start with base expression
        tpm_matrix[:, i] = base_expression * sample_factors[i]
        
        # Add tissue-specific modulation
        tpm_matrix[:, i] *= tissue_effect[tissue]
        
        # Add herbivore-specific modulation (stronger for non-housekeeping genes)
        herbivore_mod = herbivore_effect[herbivore]
        # Housekeeping genes are less affected by herbivory
        herbivore_mod[:n_housekeeping] = np.ones(n_housekeeping) * np.random.lognormal(mean=0, sigma=0.1)
        tpm_matrix[:, i] *= herbivore_mod
        
        # Ensure no zeros or negative values
        tpm_matrix[:, i] = np.maximum(tpm_matrix[:, i], 0.001)
    
    # Create DataFrame
    df = pd.DataFrame(
        tpm_matrix,
        index=gene_names,
        columns=sample_names
    )
    
    # Round to 3 decimal places for realism
    df = df.round(3)
    
    logger.info(f"Generated synthetic matrix with shape: {df.shape}")
    logger.info(f"Expression range: {df.min().min():.3f} - {df.max().max():.3f} TPM")
    
    return df

def calculate_manifest_entry(
    file_path: str,
    source_type: str = "synthetic",
    generation_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate manifest entry for a synthetic file.
    
    Args:
        file_path: Path to the file
        source_type: Type of source (should be "synthetic")
        generation_params: Parameters used for generation
        
    Returns:
        Dict containing manifest entry data
    """
    # Calculate SHA256 checksum
    checksum = compute_sha256(file_path)
    
    # Get tool versions
    tool_versions = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "project": "llmXive-plant-defense"
    }
    
    # Create provenance info
    provenance = ProvenanceInfo(
        generated_at=datetime.datetime.now().isoformat(),
        tool_versions=tool_versions,
        source_type=source_type,
        generation_params=generation_params or {}
    )
    
    # Create manifest entry
    entry = ManifestEntry(
        file_name=os.path.basename(file_path),
        checksum=checksum,
        source_type=source_type,
        provenance=provenance
    )
    
    return entry.model_dump()

def save_synthetic_manifest(
    entries: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Save a list of manifest entries to a JSON file.
    
    Args:
        entries: List of manifest entry dictionaries
        output_path: Path to save the manifest
    """
    manifest = DataManifest(
        entries=entries,
        created_at=datetime.datetime.now().isoformat(),
        version="1.0"
    )
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(manifest.model_dump(), f, indent=2)
    
    logger.info(f"Saved synthetic manifest to {output_path}")

def generate_synthetic_tpm_study(
    output_dir: str,
    n_genes: int = 20000,
    n_samples: int = 50,
    seed: Optional[int] = None,
    tissue_types: Optional[List[str]] = None,
    herbivore_types: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate a complete synthetic TPM study with matrix and metadata.
    
    Args:
        output_dir: Directory to save outputs
        n_genes: Number of genes
        n_samples: Number of samples
        seed: Random seed
        tissue_types: Tissue types
        herbivore_types: Herbivore types
        
    Returns:
        Dict with paths to generated files
    """
    config = get_config()
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating synthetic study in {output_dir}")
    
    # Generate TPM matrix
    tpm_matrix = generate_synthetic_tpm_matrix(
        n_genes=n_genes,
        n_samples=n_samples,
        seed=seed,
        tissue_types=tissue_types,
        herbivore_types=herbivore_types
    )
    
    # Save TPM matrix
    tpm_file = output_path / "synthetic_tpm_matrix.csv"
    tpm_matrix.to_csv(tpm_file)
    logger.info(f"Saved TPM matrix to {tpm_file}")
    
    # Generate metadata
    metadata = {
        "study_id": "synthetic_study_001",
        "generated_at": datetime.datetime.now().isoformat(),
        "parameters": {
            "n_genes": n_genes,
            "n_samples": n_samples,
            "seed": seed,
            "tissue_types": tissue_types,
            "herbivore_types": herbivore_types
        },
        "samples": []
    }
    
    # Add sample metadata
    for col in tpm_matrix.columns:
        parts = col.split("_")
        sample_meta = {
            "sample_id": col,
            "tissue": parts[2],
            "herbivore_type": parts[3],
            "replicate": int(parts[1])
        }
        metadata["samples"].append(sample_meta)
    
    # Save metadata
    metadata_file = output_path / "synthetic_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_file}")
    
    # Create manifest entry for TPM matrix
    tpm_params = {
        "n_genes": n_genes,
        "n_samples": n_samples,
        "seed": seed
    }
    tpm_entry = calculate_manifest_entry(
        str(tpm_file),
        source_type="synthetic",
        generation_params=tpm_params
    )
    
    # Create manifest entry for metadata
    metadata_entry = calculate_manifest_entry(
        str(metadata_file),
        source_type="synthetic",
        generation_params={"type": "metadata"}
    )
    
    # Save manifest
    manifest_path = Path(config.data_dir) / "manifests" / "synthetic_manifest.json"
    save_synthetic_manifest([tpm_entry, metadata_entry], str(manifest_path))
    
    return {
        "tpm_matrix": str(tpm_file),
        "metadata": str(metadata_file),
        "manifest": str(manifest_path)
    }

def main():
    """Main entry point for synthetic data generation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate synthetic TPM matrices for pipeline validation"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (defaults to data/synthetic/)"
    )
    parser.add_argument(
        "--n-genes",
        type=int,
        default=20000,
        help="Number of genes to generate"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=50,
        help="Number of samples to generate"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--tissue-types",
        type=str,
        nargs="+",
        default=["leaf", "root", "stem", "flower"],
        help="Tissue types to include"
    )
    parser.add_argument(
        "--herbivore-types",
        type=str,
        nargs="+",
        default=["chewing", "sucking", "none"],
        help="Herbivore types to include"
    )
    
    args = parser.parse_args()
    
    config = get_config()
    output_dir = args.output_dir or str(Path(config.data_dir) / "synthetic")
    
    logger.info("Starting synthetic data generation")
    logger.info(f"Parameters: genes={args.n_genes}, samples={args.n_samples}, seed={args.seed}")
    
    try:
        results = generate_synthetic_tpm_study(
            output_dir=output_dir,
            n_genes=args.n_genes,
            n_samples=args.n_samples,
            seed=args.seed,
            tissue_types=args.tissue_types,
            herbivore_types=args.herbivore_types
        )
        
        logger.info("Synthetic data generation completed successfully")
        logger.info(f"TPM Matrix: {results['tpm_matrix']}")
        logger.info(f"Metadata: {results['metadata']}")
        logger.info(f"Manifest: {results['manifest']}")
        
    except Exception as e:
        logger.error(f"Synthetic data generation failed: {e}")
        raise

if __name__ == "__main__":
    main()
