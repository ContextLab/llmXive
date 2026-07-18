"""
Synthetic data generator for testing the preprocessing pipeline.

Generates structurally valid synthetic FASTQ-like count data and TPM matrices
to satisfy Constitution VI (provenance, checksums) and allow testing of
batch correction and QC logic without external dependencies.
"""
import os
import json
import hashlib
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_data_path, get_housekeeping_genes
from src.utils.schemas import ProvenanceInfo, ManifestEntry, DataManifest, compute_sha256, create_manifest_entry

def generate_synthetic_counts(
    n_genes: int = 5000,
    n_samples: int = 10,
    n_batches: int = 2,
    seed: int = 42,
    output_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Generates a synthetic count matrix resembling RNA-seq output from featureCounts.
    
    Args:
        n_genes: Number of genes to simulate.
        n_samples: Number of samples.
        n_batches: Number of batches to simulate (for batch correction testing).
        seed: Random seed for reproducibility.
        output_dir: Directory to save the CSV file.
        
    Returns:
        pandas DataFrame with genes as index and samples as columns.
    """
    np.random.seed(seed)
    
    # Generate gene names
    gene_names = [f"Gene_{i}" for i in range(n_genes)]
    
    # Generate sample names
    sample_names = [f"Sample_{i}" for i in range(n_samples)]
    
    # Generate counts using negative binomial distribution (common for RNA-seq)
    # n=5, p=0.3 gives a reasonable mean/variance relationship
    counts_data = np.random.negative_binomial(n=5, p=0.3, size=(n_genes, n_samples))
    
    # Create DataFrame
    df = pd.DataFrame(counts_data, index=gene_names, columns=sample_names)
    
    # Add batch effect to a subset of genes (e.g., housekeeping genes)
    # This ensures the batch correction step has something to correct
    hk_genes = get_housekeeping_genes()
    for gene in hk_genes:
        if gene in df.index:
            # Add a systematic shift based on batch
            batch_idx = [i // (n_samples // n_batches) for i in range(n_samples)]
            shift = np.array([1000 if b == 1 else 0 for b in batch_idx])
            df.loc[gene] += shift
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "synthetic_counts.csv"
        df.to_csv(output_file)
    
    return df

def generate_synthetic_fastq_study(
    study_name: str = "synthetic_study_001",
    n_samples: int = 10,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generates a synthetic study structure including FASTQ-like files (mocked as text)
    and a manifest.
    
    Since we cannot generate real FASTQ without a sequencer, we generate text files
    that mimic the structure and checksum requirements.
    
    Returns:
        Dictionary containing paths to generated files and manifest info.
    """
    base_dir = output_dir or Path(get_data_path()) / "raw"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    manifest_entries = []
    generated_files = []
    
    for i in range(n_samples):
        file_name = f"{study_name}_sample_{i}.fastq.gz"
        file_path = base_dir / file_name
        
        # Generate a mock FASTQ content (4 lines per read, repeated)
        # This is not real sequence data but satisfies the file existence and checksum requirement
        content_lines = []
        for j in range(100): # 100 reads
            content_lines.append(f"@READ_{i}_{j}")
            content_lines.append("ACGT" * 25) # 100bp sequence
            content_lines.append("+")
            content_lines.append("!" * 100) # Quality scores
        
        content = "\n".join(content_lines)
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Calculate checksum
        checksum = compute_sha256(file_path)
        
        entry = create_manifest_entry(
            file_name=file_name,
            file_path=str(file_path),
            source_type="synthetic",
            provenance={
                "generated_at": datetime.datetime.now().isoformat(),
                "tool_versions": {
                    "python": f"{sys.version_info.major}.{sys.version_info.minor}",
                    "numpy": np.__version__
                }
            }
        )
        manifest_entries.append(entry)
        generated_files.append(str(file_path))
    
    # Write manifest
    manifest = DataManifest(entries=manifest_entries)
    manifest_path = base_dir.parent / "manifests" / f"{study_name}_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, 'w') as f:
        f.write(manifest.model_dump_json(indent=2))
    
    return {
        "study_name": study_name,
        "files": generated_files,
        "manifest_path": str(manifest_path)
    }

def calculate_tpm_from_counts(counts_df: pd.DataFrame, lengths: Optional[pd.Series] = None) -> pd.DataFrame:
    """
    Calculates TPM (Transcripts Per Million) from a count matrix.
    
    Args:
        counts_df: DataFrame of raw counts.
        lengths: Optional Series of gene lengths. If None, assumes uniform length.
        
    Returns:
        DataFrame of TPM values.
    """
    if lengths is None:
        lengths = pd.Series(1000, index=counts_df.index) # Assume 1kb uniform length
    
    # Calculate Reads Per Kilobase (RPK)
    rpk = counts_df.div(lengths, axis=0) / 1000.0
    
    # Calculate scaling factor (per million)
    scaling_factors = rpk.sum(axis=0) / 1e6
    
    # Calculate TPM
    tpm = rpk.div(scaling_factors, axis=1)
    
    return tpm
